"""Arq worker for approval-gated analysis.

Each queued job uses a deterministic Arq ID. All job analysis runs must use a
shared Postgres LangGraph checkpointer so approvals can resume in another
process. No marketplace write is executed before the graph's interrupt.
"""
from __future__ import annotations

import asyncio
import os
from arq.connections import RedisSettings
from arq.cron import cron


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(os.getenv('GIGBID_REDIS_URL','redis://localhost:6379/0'))


async def analyze_job(ctx:dict,thread_id:str,job:dict,persona:str) -> dict:
    if not os.getenv('GIGBID_CHECKPOINT_DATABASE_URL'):
        raise RuntimeError('Background agent runs require a shared Postgres checkpointer')
    from apps.api.main import bid_graph,registry,CONFIG
    owner_id=thread_id.split(':',1)[0]
    try:
        await asyncio.to_thread(bid_graph.invoke,{'job':job,'persona':persona,'owner_id':owner_id,'revision':0},
            {'configurable':{'thread_id':thread_id},'recursion_limit':int(CONFIG.get('max_steps',18))})
    except Exception as exc:
        registry.fail(thread_id,type(exc).__name__)
        raise
    return {'thread_id':thread_id,'state':'checkpointed'}


async def scout_saved_searches(ctx:dict)->dict:
    """Hourly scanner: each search is limited to one run per >=4 hours."""
    from apps.api.main import saved_searches,registry,marketplace_for
    queued=0
    for saved in saved_searches.due():
        for job in marketplace_for(saved['owner_id']).search_jobs(saved['query']):
            if saved_searches.seen(saved['id'],job['id']):continue
            thread_id=f"{saved['owner_id']}:{saved['persona']}:{job['id']}:{saved['id']}"
            job_id=f"gigbid:scout:{saved['id']}:{job['id']}"
            result=await ctx['redis'].enqueue_job('analyze_job',thread_id,job,saved['persona'],_job_id=job_id)
            if result is not None:
                registry.add(thread_id,'bid',saved['owner_id'])
                saved_searches.mark_seen(saved['id'],job['id'])
                queued+=1
        saved_searches.mark_run(saved['id'])
    return {'queued':queued}


class WorkerSettings:
    functions=[analyze_job,scout_saved_searches]
    cron_jobs=[cron(scout_saved_searches,minute=0)]
    redis_settings=redis_settings()
    max_jobs=4
    job_timeout=600
    max_tries=3
    keep_result=3600
