"""Arq worker for approval-gated analysis.

Each queued job uses a deterministic Arq ID. All job analysis runs must use a
shared Postgres LangGraph checkpointer so approvals can resume in another
process. No marketplace write is executed before the graph's interrupt.
"""
from __future__ import annotations

import asyncio
import os
from arq.connections import RedisSettings


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(os.getenv('GIGBID_REDIS_URL','redis://localhost:6379/0'))


async def analyze_job(ctx:dict,thread_id:str,job:dict,persona:str) -> dict:
    if not os.getenv('GIGBID_CHECKPOINT_DATABASE_URL'):
        raise RuntimeError('Background agent runs require a shared Postgres checkpointer')
    from apps.api.main import bid_graph
    owner_id=thread_id.split(':',1)[0]
    await asyncio.to_thread(bid_graph.invoke,{'job':job,'persona':persona,'owner_id':owner_id,'revision':0},
                            {'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,'state':'checkpointed'}


class WorkerSettings:
    functions=[analyze_job]
    redis_settings=redis_settings()
    max_jobs=4
    job_timeout=600
    max_tries=3
    keep_result=3600
