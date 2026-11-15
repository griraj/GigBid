"""Single application-facing marketplace interface; no web route calls an adapter directly."""
from __future__ import annotations
import json
import sqlite3
import threading
import time
from pathlib import Path
from data.synthetic import JOBS, CLIENTS
from data.ingest import load_jobs
import re

def mask_pii(obj):
    """Redact contact and payment markers in audit copies, not submitted text."""
    encoded=json.dumps(obj)
    encoded=re.sub(r'[\w.%-]+@[\w.-]+\.[a-zA-Z]{2,}','[EMAIL_REDACTED]',encoded)
    encoded=re.sub(r'(?<!\d)(?:\+?\d[\d ()-]{8,}\d)(?!\d)','[PHONE_REDACTED]',encoded)
    encoded=re.sub(r'\b\d{13,19}\b','[PAYMENT_NUMBER_REDACTED]',encoded)
    return encoded

class MarketplaceUnavailable(RuntimeError): pass

class LocalMarketplace:
    def __init__(self, path='gigbid.sqlite'):
        self.db=sqlite3.connect(path,check_same_thread=False)
        self.lock=threading.RLock()
        with self.db:
            self.db.execute('create table if not exists writes (key text primary key, kind text, result text, created real)')
            self.db.execute('create table if not exists audit (id integer primary key, actor text, tool text, args text, result text, trace_id text, at real)')
            self.db.execute('create table if not exists messages (id integer primary key, job_id text, sender text, body text, created real)')
        self.initial_balance=100

    def search_jobs(self, query=''):
        records=JOBS+load_jobs()
        return [j for j in records if query.lower() in (j['title']+' '+j['description']).lower()]

    def get_job(self,id):
        return next((j for j in self.search_jobs() if j['id']==id),None)

    def get_client_history(self,id): return CLIENTS.get(id,{})
    def get_connects_balance(self):
        spent=0
        for (raw,) in self.db.execute("select result from writes where kind='submit_proposal'"):
            spent+=json.loads(raw).get('connects_cost',0)
        return max(0,self.initial_balance-spent)
    def list_messages(self,job_id):
        return [dict(id=r[0],sender=r[1],body=r[2]) for r in self.db.execute('select id,sender,body from messages where job_id=? order by id',(job_id,))]

    def _write(self,kind,payload,key,dry_run=False,actor='reviewer',trace_id=''):
        if not key or len(key)<8: raise ValueError('idempotency_key must contain at least 8 characters')
        job=self.get_job(payload['job_id'])
        if job is None:raise ValueError('Unknown job')
        if job.get('provenance',{}).get('kind')=='real_export':
            raise ValueError('Imported job is research-only; cannot submit to external marketplaces in local mode')
        preview={'kind':kind,'payload':payload,'connects_cost':job['connects'] if kind=='submit_proposal' else 0,'dry_run':dry_run}
        if dry_run: return preview
        with self.lock:
            row=self.db.execute('select result from writes where key=?',(key,)).fetchone()
            if row: return json.loads(row[0])
            if kind=='submit_proposal':
                if self.get_connects_balance()<preview['connects_cost']: raise ValueError('Insufficient Connects')
            result={**preview,'dry_run':False,'status':'created' if kind=='create_proposal_draft' else 'submitted','idempotency_key':key}
            with self.db:
                if kind=='send_message': self.db.execute('insert into messages(job_id,sender,body,created) values(?,?,?,?)',(payload['job_id'],'freelancer',payload['body'],time.time()))
                self.db.execute('insert into writes values(?,?,?,?)',(key,kind,json.dumps(result),time.time()))
                self.db.execute('insert into audit(actor,tool,args,result,trace_id,at) values(?,?,?,?,?,?)',(actor,kind,mask_pii(payload),mask_pii(result),trace_id,time.time()))
            return result

    def create_proposal_draft(self,job_id,text,key,dry_run=False,**meta): return self._write('create_proposal_draft',{'job_id':job_id,'text':text},key,dry_run,**meta)
    def submit_proposal(self,job_id,text,key,dry_run=False,**meta): return self._write('submit_proposal',{'job_id':job_id,'text':text},key,dry_run,**meta)
    def send_message(self,job_id,body,key,dry_run=False,**meta): return self._write('send_message',{'job_id':job_id,'body':body},key,dry_run,**meta)

class GigSimMarketplace:
    """External GigSim HTTP adapter; actual paths must be verified with the instructor service."""
    def __init__(self,url,token):
        import httpx
        self.client=httpx.Client(base_url=url,headers={'Authorization':f'Bearer {token}'},timeout=10)
    def _call(self,method,path,**kwargs):
        import httpx
        try:
            r=self.client.request(method,path,**kwargs);r.raise_for_status();return r.json()
        except httpx.HTTPError as exc: raise MarketplaceUnavailable(str(exc)) from exc
    def search_jobs(self,query=''): return self._call('GET','/jobs',params={'q':query})
    def get_job(self,id): return self._call('GET',f'/jobs/{id}')
    def get_client_history(self,id): return self._call('GET',f'/clients/{id}')
    def get_connects_balance(self): return self._call('GET','/connects')
    def list_messages(self,job_id): return self._call('GET',f'/jobs/{job_id}/messages')
    def _write(self,path,payload,key,dry_run): return self._call('POST',path,json={**payload,'dry_run':dry_run},headers={'Idempotency-Key':key})
    def create_proposal_draft(self,job_id,text,key,dry_run=False,**kwargs): return self._write('/proposals/drafts',{'job_id':job_id,'text':text},key,dry_run)
    def submit_proposal(self,job_id,text,key,dry_run=False,**kwargs): return self._write('/proposals',{'job_id':job_id,'text':text},key,dry_run)
    def send_message(self,job_id,body,key,dry_run=False,**kwargs): return self._write('/messages',{'job_id':job_id,'body':body},key,dry_run)

def build_marketplace(mode='local',db_path='gigbid.sqlite'):
    import os
    if mode=='local': return LocalMarketplace(db_path)
    if mode=='gigsim': return GigSimMarketplace(os.environ['GIGBID_GIGSIM_URL'],os.environ['GIGBID_GIGSIM_TOKEN'])
    if mode=='upwork': raise MarketplaceUnavailable('Upwork OAuth connection has not been authorized; live mode disabled safely')
    raise ValueError('Unknown marketplace mode')
