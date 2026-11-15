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
from rag.retriever import EvidenceIndex
import json

ROOT=Path(__file__).resolve().parents[2]
CONFIG=yaml.safe_load((ROOT/'agent/config.yaml').read_text())
marketplace=build_marketplace(os.getenv('GIGBID_MODE','local'),os.getenv('GIGBID_DB_PATH',str(ROOT/'gigbid.sqlite')))
index=EvidenceIndex(EVIDENCE)
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    db=sqlite3.connect(str(ROOT/'checkpoints.sqlite'),check_same_thread=False)
    checkpointer=SqliteSaver(db)
except ImportError:
    checkpointer=MemorySaver()  # degraded: approval is not restart-durable
bid_graph=build_bid_graph(marketplace,index,CONFIG,checkpointer)
conversation_graph=build_conversation_graph(marketplace,checkpointer)
jobs_lock=threading.Lock()
run_personas={}

app=FastAPI(title='GigBid API',version='0.1.0',description='Evidence-first approval-gated freelancer copilot')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:5173','http://localhost:3000'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])

def guard(authorization:str|None):
    expected=os.getenv('GIGBID_API_TOKEN','demo-reviewer-token')
    if authorization!=f'Bearer {expected}':raise HTTPException(401,'Invalid reviewer token')

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
def health():return {'status':'ok','mode':os.getenv('GIGBID_MODE','local'),'durable':type(checkpointer).__name__=='SqliteSaver'}

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
    guard(authorization);return [e for e in EVIDENCE if e['persona']==persona]

@app.post('/runs')
def start_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    guard(authorization);j=marketplace.get_job(req.job_id)
    if not j:raise HTTPException(404,'Job not found')
    thread_id=f'{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    with jobs_lock:
        run_personas[thread_id]=req.persona
        bid_graph.invoke({'job':j,'persona':req.persona,'revision':0},config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**get_run_state(thread_id)}

def get_run_state(thread_id):
    snapshot=bid_graph.get_state({'configurable':{'thread_id':thread_id}})
    if not snapshot.values:raise HTTPException(404,'Run not found')
    values=dict(snapshot.values)
    values['pending_approval']=bool(snapshot.interrupts)
    values['interrupt_payload']=[i.value for i in snapshot.interrupts]
    return values

@app.get('/runs/{thread_id}')
def run_state(thread_id:str,authorization:str|None=Header(None)):
    guard(authorization);return {'thread_id':thread_id,**get_run_state(thread_id)}

@app.post('/runs/{thread_id}/approval')
def approve_run(thread_id:str,req:ApprovalRequest,authorization:str|None=Header(None)):
    guard(authorization)
    if not get_run_state(thread_id)['pending_approval']:raise HTTPException(409,'No pending approval')
    choice=req.model_dump(exclude_none=True)
    with jobs_lock:bid_graph.invoke(Command(resume=choice),config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**get_run_state(thread_id)}

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
