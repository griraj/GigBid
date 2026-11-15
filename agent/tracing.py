"""Local redacted trace correlation; hosted LangSmith remains opt-in."""
import json
import threading
from contextvars import ContextVar
from datetime import datetime,timezone
from agent.paths import data_path
from agent.marketplace_port import mask_pii

trace_id=ContextVar('gigbid_trace_id',default='')
_lock=threading.Lock()


def event(kind,**fields):
    record={'at':datetime.now(timezone.utc).isoformat(),'trace_id':trace_id.get(),'kind':kind,**fields}
    with _lock:
        with data_path('traces.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(mask_pii(record)+'\n')
