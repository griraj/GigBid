from __future__ import annotations
import os
import sqlite3
import threading
from pathlib import Path
from uuid import uuid4
from contextlib import asynccontextmanager
from functools import lru_cache
import yaml
from fastapi import FastAPI,HTTPException,Header,UploadFile,File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse,RedirectResponse
from urllib.parse import urlencode
import httpx
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
from agent.paragraphs import regenerate_paragraph
from apps.api.auth.accounts import Accounts
from apps.api.auth.oauth import from_environment
from data.portfolio_store import PortfolioStore
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
accounts=Accounts(data_path('accounts.sqlite'))
uploads=PortfolioStore(data_path('portfolio_uploads.sqlite'))
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
    if os.getenv('GIGBID_AUTH_MODE','reviewer')=='multi':
        if not authorization or not authorization.startswith('Bearer '):
            raise HTTPException(401,'Missing access token')
        identity=accounts.identity(authorization[7:])
        if identity is None:raise HTTPException(401,'Invalid or expired access token')
        return identity['id']
    expected=os.getenv('GIGBID_API_TOKEN','demo-reviewer-token')
    if not secrets.compare_digest(authorization or '',f'Bearer {expected}'):raise HTTPException(401,'Invalid reviewer token')
    return 'reviewer'

def owned_thread(thread_id:str,authorization:str|None):
    owner=guard(authorization)
    if not registry.owns(thread_id,owner):raise HTTPException(404,'Run not found')
    return owner

class Credentials(BaseModel):
    email:str=Field(min_length=3,max_length=254)
    password:str=Field(min_length=12,max_length=256)
    invite_code:str|None=None

@app.post('/auth/register')
def register_account(req:Credentials):
    if os.getenv('GIGBID_AUTH_MODE','reviewer')!='multi':
        raise HTTPException(403,'Account registration is disabled in reviewer mode')
    invite=os.getenv('GIGBID_SIGNUP_INVITE','')
    if not invite:
        raise HTTPException(403,'Registration is disabled until an invitation secret is configured')
    if not secrets.compare_digest(req.invite_code or '',invite):
        raise HTTPException(403,'Invalid invitation')
    try:return accounts.register(req.email,req.password)
    except ValueError as exc:raise HTTPException(409,str(exc)) from exc

@app.post('/auth/login')
def login_account(req:Credentials):
    if os.getenv('GIGBID_AUTH_MODE','reviewer')!='multi':
        raise HTTPException(403,'Account login is disabled in reviewer mode')
    result=accounts.login(req.email,req.password)
    if result is None:raise HTTPException(401,'Invalid credentials')
    return result

@app.get('/auth/me')
def account_me(authorization:str|None=Header(None)):
    owner=guard(authorization)
    if owner=='reviewer':return {'id':'reviewer','role':'demo'}
    return accounts.identity((authorization or '')[7:])

@app.post('/auth/logout')
def logout_account(authorization:str|None=Header(None)):
    guard(authorization)
    if os.getenv('GIGBID_AUTH_MODE','reviewer')=='multi':accounts.logout((authorization or '')[7:])
    return {'logged_out':True}

@lru_cache(maxsize=1)
def oauth_vault():
    try:return from_environment(data_path('oauth.sqlite'))
    except (ValueError,TypeError) as exc:
        raise HTTPException(503,'OAuth token storage is not configured') from exc

@app.get('/auth/connections')
def oauth_connections(authorization:str|None=Header(None)):
    return {'providers':oauth_vault().connected(guard(authorization))}

@app.post('/auth/github/start')
def github_oauth_start(authorization:str|None=Header(None)):
    owner=guard(authorization)
    client_id=os.getenv('GIGBID_GITHUB_OAUTH_CLIENT_ID','')
    base=os.getenv('GIGBID_PUBLIC_BASE_URL','').rstrip('/')
    if not client_id or not base.startswith('https://'):
        raise HTTPException(503,'GitHub OAuth client ID and HTTPS public URL are required')
    state=oauth_vault().begin(owner,'github')
    callback=base+'/api/auth/github/callback'
    url='https://github.com/login/oauth/authorize?'+urlencode({'client_id':client_id,
         'redirect_uri':callback,'state':state,'scope':'read:user'})
    return {'authorization_url':url}

@app.get('/auth/github/callback')
async def github_oauth_callback(code:str='',state:str=''):
    owner=oauth_vault().consume(state,'github')
    if not owner:raise HTTPException(400,'OAuth state is invalid or expired')
    secret=os.getenv('GIGBID_GITHUB_OAUTH_CLIENT_SECRET','')
    client_id=os.getenv('GIGBID_GITHUB_OAUTH_CLIENT_ID','')
    if not secret or not client_id:raise HTTPException(503,'GitHub OAuth credentials are not configured')
    async with httpx.AsyncClient(timeout=12) as client:
        response=await client.post('https://github.com/login/oauth/access_token',
            data={'client_id':client_id,'client_secret':secret,'code':code},
            headers={'Accept':'application/json'})
    if response.status_code!=200:raise HTTPException(502,'GitHub OAuth exchange failed')
    token=response.json().get('access_token')
    if not token:raise HTTPException(502,'GitHub did not issue an access token')
    oauth_vault().save(owner,'github',token)
    return RedirectResponse(url='/?connected=github',status_code=303)

@app.delete('/auth/connections/{provider}')
def oauth_disconnect(provider:str,authorization:str|None=Header(None)):
    owner=guard(authorization)
    if provider!='github':raise HTTPException(404,'Unknown provider')
    return {'disconnected':oauth_vault().disconnect(owner,provider)}

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

class RegenerateRequest(BaseModel):
    paragraph_index:int=Field(ge=0,le=50)
    text:str=Field(min_length=1,max_length=15000)

@app.post('/runs/queue',status_code=202)
async def queue_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    """Enqueue analysis on an Arq worker; clients poll /runs/{id} for updates."""
    owner=guard(authorization)
    if not os.getenv('GIGBID_REDIS_URL') or not os.getenv('GIGBID_CHECKPOINT_DATABASE_URL'):
        raise HTTPException(503,'Background runs require Redis and shared Postgres checkpoints')
    job=marketplace.get_job(req.job_id)
    if job is None:raise HTTPException(404,'Job not found')
    from arq.connections import create_pool
    from worker.jobs import redis_settings
    thread_id=f'{owner}:{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    registry.add(thread_id,'bid',owner)
    pool=await create_pool(redis_settings())
    try:
        queued=await pool.enqueue_job('analyze_job',thread_id,job,req.persona,
                                      _job_id=f'gigbid:analysis:{thread_id}')
    finally:
        await pool.aclose()
    if queued is None:raise HTTPException(409,'Analysis already queued')
    return {'thread_id':thread_id,'status':'queued','queue_job_id':queued.job_id}

@app.get('/health')
def health():
    ephemeral=os.getenv('GIGBID_STORAGE_EPHEMERAL','false').lower()=='true'
    return {'status':'ok','mode':os.getenv('GIGBID_MODE','local'),
        'auth_mode':os.getenv('GIGBID_AUTH_MODE','reviewer'),
        'queue_enabled':bool(os.getenv('GIGBID_REDIS_URL') and os.getenv('GIGBID_CHECKPOINT_DATABASE_URL')),
        'rag_backend':os.getenv('GIGBID_RAG_BACKEND','lexical'),'tool_backend':os.getenv('GIGBID_TOOL_BACKEND','mcp'),
        'durable':not ephemeral and type(checkpointer).__name__ in ('SqliteSaver','PostgresSaver'),
        'storage_ephemeral':ephemeral,'mcp_sessions':'persistent' if os.getenv('GIGBID_MCP_PERSISTENT','1')!='0' else 'fresh',
        'revision':os.getenv('RENDER_GIT_COMMIT','local')}

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
    owner=guard(authorization)
    return [e for e in portfolio_items if e['persona']==persona]+uploads.list(owner)

@app.post('/portfolio/upload',status_code=201)
async def upload_portfolio(file:UploadFile=File(...),authorization:str|None=Header(None)):
    owner=guard(authorization)
    filename=(file.filename or 'upload').split('/')[-1].split('\\')[-1][:120]
    suffix=Path(filename).suffix.lower()
    if suffix not in ('.txt','.md','.pdf'):
        raise HTTPException(415,'Accepted portfolio formats: TXT, Markdown, PDF')
    content=await file.read(500001)
    if len(content)>500000:raise HTTPException(413,'Upload is limited to 500 KB')
    try:
        if suffix=='.pdf':
            from io import BytesIO
            from pypdf import PdfReader
            reader=PdfReader(BytesIO(content),strict=False)
            if len(reader.pages)>50:raise HTTPException(413,'PDF exceeds 50 pages')
            body='\n'.join(page.extract_text() or '' for page in reader.pages)
        else:body=content.decode('utf-8')
    except Exception as exc:
        if isinstance(exc,HTTPException):raise
        raise HTTPException(422,'Could not extract text from document') from exc
    try:return uploads.add(owner,filename,body)
    except ValueError as exc:raise HTTPException(422,str(exc)) from exc

@app.delete('/portfolio/upload/{item_id}')
def delete_portfolio_upload(item_id:str,authorization:str|None=Header(None)):
    owner=guard(authorization)
    if not uploads.delete(owner,item_id):raise HTTPException(404,'Upload not found')
    return {'deleted':True}

@app.post('/runs')
def start_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    owner=guard(authorization);j=marketplace.get_job(req.job_id)
    if not j:raise HTTPException(404,'Job not found')
    thread_id=f'{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    registry.add(thread_id,'bid',owner)
    with jobs_lock:
        run_personas[thread_id]=req.persona
    bid_graph.invoke({'job':j,'persona':req.persona,'owner_id':owner,'revision':0},config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**get_run_state(thread_id)}


@app.get('/runs')
def list_runs(authorization:str|None=Header(None)):
    owner=guard(authorization)
    result=[]
    for thread_id,created in registry.list('bid',owner_id=owner):
        try:result.append({'thread_id':thread_id,'created':created,**get_run_state(thread_id)})
        except HTTPException as exc:
            if exc.status_code!=404:raise
    return result


@app.post('/runs/stream')
def stream_run(req:AnalyzeRequest,authorization:str|None=Header(None)):
    owner=guard(authorization)
    job=marketplace.get_job(req.job_id)
    if not job:raise HTTPException(404,'Job not found')
    thread_id=f'{req.persona}:{req.job_id}:{uuid4().hex[:12]}'
    def events():
        try:
            registry.add(thread_id,'bid',owner)
            yield f'event: started\ndata: {json.dumps({"thread_id":thread_id})}\n\n'
            with jobs_lock:
                for update in bid_graph.stream({'job':job,'persona':req.persona,'owner_id':owner,'revision':0},
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
    if not snapshot.values:
        if registry.exists(thread_id):return {'status':'queued','pending_approval':False,'interrupt_payload':[]}
        raise HTTPException(404,'Run not found')
    values=dict(snapshot.values)
    values.setdefault('status','needs_attention')
    values['pending_approval']=bool(snapshot.interrupts)
    values['interrupt_payload']=[i.value for i in snapshot.interrupts]
    return values

@app.get('/runs/{thread_id}')
def run_state(thread_id:str,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization);return {'thread_id':thread_id,**get_run_state(thread_id)}

@app.get('/runs/{thread_id}/history')
def run_history(thread_id:str,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization)
    get_run_state(thread_id)
    snapshots=list(bid_graph.get_state_history({'configurable':{'thread_id':thread_id}},limit=100))
    return {'thread_id':thread_id,'snapshots':[
        {'checkpoint_id':s.config.get('configurable',{}).get('checkpoint_id'),
         'created_at':s.created_at,'next':list(s.next),
         'status':s.values.get('status'),'source':s.metadata.get('source') if s.metadata else None}
        for s in snapshots],
        'note':'Read-only checkpoint inspection; no marketplace actions are replayed.'}

@app.post('/runs/{thread_id}/regenerate-paragraph')
def regenerate_run_paragraph(thread_id:str,req:RegenerateRequest,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization)
    state=get_run_state(thread_id)
    if not state['pending_approval'] or state.get('status')!='awaiting_approval':
        raise HTTPException(409,'Proposal is not awaiting human approval')
    if not state.get('draft'):
        raise HTTPException(409,'No draft available')
    try:
        return regenerate_paragraph(req.text,req.paragraph_index,state.get('evidence',[]))
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc

@app.post('/runs/{thread_id}/approval')
def approve_run(thread_id:str,req:ApprovalRequest,authorization:str|None=Header(None)):
    owner=owned_thread(thread_id,authorization)
    pending=get_run_state(thread_id)
    if not pending['pending_approval']:raise HTTPException(409,'No pending approval')
    choice=req.model_dump(exclude_none=True)
    with jobs_lock:bid_graph.invoke(Command(resume=choice),config={'configurable':{'thread_id':thread_id}})
    finished=get_run_state(thread_id)
    if finished['status']=='submitted' and req.action=='approve' and req.text and req.text!=pending.get('draft',{}).get('text'):
        memory.record_approved_edit(owner,pending['draft']['text'],req.text)
    return {'thread_id':thread_id,**finished}

@app.get('/memory')
def get_memory(authorization:str|None=Header(None)):
    return memory.list(guard(authorization))

@app.delete('/memory/{memory_id}')
def delete_memory(memory_id:int,authorization:str|None=Header(None)):
    owner=guard(authorization)
    if not memory.delete(owner,memory_id):raise HTTPException(404,'Memory not found')
    return {'deleted':True}

@app.get('/runs/{thread_id}/events')
def run_events(thread_id:str,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization)
    def events():
        state=get_run_state(thread_id)
        for name in ['spec','risk','fit','decision','price','draft','critique','compliance','status']:
            if name in state:yield f'event: node\ndata: {json.dumps({"node":name,"value":state[name]})}\n\n'
        yield 'event: done\ndata: {}\n\n'
    return StreamingResponse(events(),media_type='text/event-stream')

@app.post('/conversations')
def start_conversation(req:MessageRequest,authorization:str|None=Header(None)):
    owner=guard(authorization);thread_id=f'conversation:{uuid4().hex}'
    registry.add(thread_id,'conversation',owner)
    conversation_graph.invoke(req.model_dump(),config={'configurable':{'thread_id':thread_id}})
    return {'thread_id':thread_id,**conversation_state(thread_id)}

def conversation_state(thread_id):
    s=conversation_graph.get_state({'configurable':{'thread_id':thread_id}})
    if not s.values:raise HTTPException(404,'Conversation not found')
    return {**s.values,'pending_approval':bool(s.interrupts)}

@app.get('/conversations/{thread_id}')
def get_conversation(thread_id:str,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization);return conversation_state(thread_id)

@app.post('/conversations/{thread_id}/approval')
def approve_conversation(thread_id:str,req:ApprovalRequest,authorization:str|None=Header(None)):
    owned_thread(thread_id,authorization)
    if not conversation_state(thread_id)['pending_approval']:raise HTTPException(409,'No pending approval')
    conversation_graph.invoke(Command(resume=req.model_dump(exclude_none=True)),config={'configurable':{'thread_id':thread_id}})
    return conversation_state(thread_id)

@app.get('/analytics')
def analytics(authorization:str|None=Header(None)):
    guard(authorization)
    if not hasattr(marketplace,'db'):return {'message':'Available in local mode'}
    rows=marketplace.db.execute('select kind,count(*) from writes group by kind').fetchall()
    return {'actions':dict(rows),'connects_remaining':marketplace.get_connects_balance(),'source':'local synthetic simulator'}
