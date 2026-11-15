from __future__ import annotations
import os
import sqlite3
import threading
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager
import yaml
from fastapi import FastAPI,HTTPException,Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel,Field
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from agent.marketplace_port import build_marketplace,MarketplaceUnavailable
from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.conversation_graph import build_conversation_graph
from data.synthetic import EVIDENCE
from rag.ingest_portfolio import load_portfolio
from rag.retriever import EvidenceIndex
from agent.memory.store import MemoryStore
from agent.paths import data_path,marketplace_path
from agent.runs import RunRegistry
import secrets
from agent.tracing import trace_id,event
import json

ROOT=Path(__file__).resolve().parents[2]
CONFIG=yaml.safe_load((ROOT/'agent/config.yaml').read_text())
marketplace=build_marketplace(os.getenv('GIGBID_MODE','local'),marketplace_path())
portfolio_items=EVIDENCE+load_portfolio()
if os.getenv('GIGBID_RAG_BACKEND','lexical')=='ollama-vector':
    from rag.ollama_vector import build_ollama_index
    index=build_ollama_index(portfolio_items)
elif os.getenv('GIGBID_RAG_BACKEND','lexical')=='neural':
    from rag.neural import NeuralEvidenceIndex
    index=NeuralEvidenceIndex(portfolio_items,
          model_name=os.getenv('GIGBID_EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'),
          directory=str(ROOT/'data/processed/chroma'))
else:index=EvidenceIndex(portfolio_items)
if os.getenv('GIGBID_CHECKPOINT_DATABASE_URL'):
    from langgraph.checkpoint.postgres import PostgresSaver
    _pg_context=PostgresSaver.from_conn_string(os.environ['GIGBID_CHECKPOINT_DATABASE_URL'])
    checkpointer=_pg_context.__enter__()
    checkpointer.setup()
else:
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        db=sqlite3.connect(str(data_path('checkpoints.sqlite')),check_same_thread=False)
        checkpointer=SqliteSaver(db)
    except ImportError:
        checkpointer=MemorySaver()  # degraded: approval is not restart-durable
bid_graph=build_bid_graph(marketplace,index,CONFIG,checkpointer)
conversation_graph=build_conversation_graph(marketplace,checkpointer)
memory=MemoryStore(data_path('memory.sqlite'))
registry=RunRegistry(data_path('runs.sqlite'))
jobs_lock=threading.Lock()
run_personas={}

if os.getenv('GIGBID_ENV')=='production' and os.getenv('GIGBID_API_TOKEN','') in ('','demo-reviewer-token','change-this-before-deploying'):
    raise RuntimeError('Set a private GIGBID_API_TOKEN before starting production')
app=FastAPI(title='GigBid API',version='0.1.0',description='Evidence-first approval-gated freelancer copilot')
app.add_middleware(CORSMiddleware,allow_origins=[v.strip() for v in os.getenv('GIGBID_CORS_ORIGINS','http://localhost:5173,http://localhost:3000').split(',') if v.strip()],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

@app.middleware('http')
async def correlate_request(request,call_next):
    identifier=uuid4().hex
    reset=trace_id.set(identifier)
    try:
        response=await call_next(request)
        response.headers['X-Trace-ID']=identifier
        event('http',method=request.method,path=request.url.path,status=response.status_code)
        return response
    finally:trace_id.reset(reset)

def guard(authorization:str|None):
    expected=os.getenv('GIGBID_API_TOKEN','demo-reviewer-token')
    if not secrets.compare_digest(authorization or '',f'Bearer {expected}'):raise HTTPException(401,'Invalid reviewer token')

class AnalyzeRequest(BaseModel):
    job_id:str
    persona:str=Field(pattern='^(ai|web|analytics)$')

class ApprovalRequest(BaseModel):
    action:str=Field(pattern='^(approve|reject)$')
    text:str|None=None
    reason:str|None=None

class MessageRequest(BaseModel):
    job_id:str
    incoming:str=Field(min_length=1,max_length=5000)

@app.get('/health')
def health():return {'status':'ok','mode':os.getenv('GIGBID_MODE','local'),'rag_backend':os.getenv('GIGBID_RAG_BACKEND','lexical'),'tool_backend':os.getenv('GIGBID_TOOL_BACKEND','mcp'),'durable':type(checkpointer).__name__ in ('SqliteSaver','PostgresSaver')}

@app.get('/jobs')
def jobs(authorization:str|None=Header(None)):
    guard(authorization)
    try:return marketplace.search_jobs()
    except MarketplaceUnavailable as exc:raise HTTPException(503, f'Marketplace unavailable: {exc}')

@app.get('/jobs/{job_id}')
def job_detail(job_id:str,authorization:str|None=Header(None)):
    guard(authorization);j=marketplace.get_job(job_id)
    if not j:raise HTTPException(404,'Job not found')
    return j

@app.get('/portfolio')
def portfolio(persona:str='ai',authorization:str|None=Header(None)):
    guard(authorization);return [e for e in portfolio_items if e['persona']==persona]

@app.post('/runs')
def start_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    guard(authorization);j=marketplace.get_job(req.job_id)
    if not j:raise HTTPException(404,'Job not found')
    thread_id=f'{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    registry.add(thread_id,'bid')
    with jobs_lock:
        run_personas[thread_id]=req.persona
        bid_graph.invoke({'job':j,'persona':req.persona,'revision':0},config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**get_run_state(thread_id)}


@app.get('/runs')
def list_runs(authorization:str|None=Header(None)):
    guard(authorization)
    result=[]
    for thread_id,created in registry.list('bid'):
        try:result.append({'thread_id':thread_id,'created':created,**get_run_state(thread_id)})
        except HTTPException as exc:
            if exc.status_code!=404:raise
    return result


@app.post('/runs/stream')
def stream_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    guard(authorization)
    job=marketplace.get_job(req.job_id)
    if not job:raise HTTPException(404,'Job not found')
    thread_id=f'{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    def events():
        try:
            registry.add(thread_id,'bid')
            yield f'event: started\ndata: {json.dumps({"thread_id":thread_id})}\n\n'
            with jobs_lock:
                for update in bid_graph.stream({'job':job,'persona':req.persona,'revision':0},
                        config={'configurable':{'thread_id':thread_id}},stream_mode='updates'):
                    for node in update:
                        if node!='__interrupt__':
                            yield f'event: node\ndata: {json.dumps({"node":node})}\n\n'
            yield f'event: done\ndata: {json.dumps({"thread_id":thread_id,**get_run_state(thread_id)},default=str)}\n\n'
        except Exception:
            yield 'event: error\ndata: {"detail":"Analysis interrupted. Marketplace or model unavailable; retry from the inbox."}\n\n'
    return StreamingResponse(events(),media_type='text/event-stream',
        headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

def get_run_state(thread_id):
    snapshot=bid_graph.get_state({'configurable':{'thread_id':thread_id}})
    if not snapshot.values:raise HTTPException(404,'Run not found')
    values=dict(snapshot.values)
    values.setdefault('status','needs_attention')
    values['pending_approval']=bool(snapshot.interrupts)
    values['interrupt_payload']=[i.value for i in snapshot.interrupts]
    return values

@app.get('/runs/{thread_id}')
def run_state(thread_id:str,authorization:str|None=Header(None)):
    guard(authorization);return {'thread_id':thread_id,**get_run_state(thread_id)}

@app.post('/runs/{thread_id}/approval')
def approve_run(thread_id:str,req:ApprovalRequest,authorization:str|None=Header(None)):
    guard(authorization)
    pending=get_run_state(thread_id)
    if not pending['pending_approval']:raise HTTPException(409,'No pending approval')
    choice=req.model_dump(exclude_none=True)
    with jobs_lock:bid_graph.invoke(Command(resume=choice),config={'configurable':{'thread_id':thread_id}})
    finished=get_run_state(thread_id)
    if finished['status']=='submitted' and req.action=='approve' and req.text and req.text!=pending.get('draft',{}).get('text'):
        memory.record_approved_edit('reviewer',pending['draft']['text'],req.text)
    return {'thread_id':thread_id,**finished}

@app.get('/memory')
def get_memory(authorization:str|None=Header(None)):
    guard(authorization);return memory.list('reviewer')

@app.delete('/memory/{memory_id}')
def delete_memory(memory_id:int,authorization:str|None=Header(None)):
    guard(authorization)
    if not memory.delete('reviewer',memory_id):raise HTTPException(404,'Memory not found')
    return {'deleted':True}

@app.get('/runs/{thread_id}/events')
def run_events(thread_id:str,authorization:str|None=Header(None)):
    guard(authorization)
    def events():
        state=get_run_state(thread_id)
        for name in ['spec','risk','fit','decision','price','draft','critique','compliance','status']:
            if name in state:yield f'event: node\ndata: {json.dumps({"node":name,"value":state[name]})}\n\n'
        yield 'event: done\ndata: {}\n\n'
    return StreamingResponse(events(),media_type='text/event-stream')

@app.post('/conversations')
def start_conversation(req:MessageRequest,authorization:str|None=Header(None)):
    guard(authorization);thread_id=f'conversation:{uuid4().hex}'
    conversation_graph.invoke(req.model_dump(),config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**conversation_state(thread_id)}

def conversation_state(thread_id):
    s=conversation_graph.get_state({'configurable':{'thread_id':thread_id}})
    if not s.values:raise HTTPException(404,'Conversation not found')
    return {**s.values,'pending_approval':bool(s.interrupts)}

@app.get('/conversations/{thread_id}')
def get_conversation(thread_id:str,authorization:str|None=Header(None)):
    guard(authorization);return conversation_state(thread_id)

@app.post('/conversations/{thread_id}/approval')
def approve_conversation(thread_id:str,req:ApprovalRequest,authorization:str|None=Header(None)):
    guard(authorization)
    if not conversation_state(thread_id)['pending_approval']:raise HTTPException(409,'No pending approval')
    conversation_graph.invoke(Command(resume=req.model_dump(exclude_none=True)),config={'configurable':{'thread_id':thread_id}})
    return conversation_state(thread_id)

@app.get('/analytics')
def analytics(authorization:str|None=Header(None)):
    guard(authorization)
    if not hasattr(marketplace,'db'):return {'message':'Available in local mode'}
    rows=marketplace.db.execute('select kind,count(*) from writes group by kind').fetchall()
    return {'actions':dict(rows),'connects_remaining':marketplace.get_connects_balance(),'source':'local synthetic simulator'}
