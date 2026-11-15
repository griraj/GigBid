"""Tenant-scoped, explicit-promotion memory over LangGraph's Store protocol.

Production uses PostgresStore; tests use InMemoryStore with the same interface.
Raw job posts, tool observations and unapproved edits never enter memory.
"""
from __future__ import annotations

import hashlib
import threading
import time
from agent.memory.store import STYLE_SIGNALS


def memory_identifier(category:str,key:str)->int:
    return int(hashlib.sha256(f'{category}:{key}'.encode()).hexdigest()[:14],16)


class LangGraphMemory:
    def __init__(self,store):
        self.store=store
        self.lock=threading.RLock()

    def _memory_namespace(self,user_id):return ('gigbid',user_id,'memory')
    def _edits_namespace(self,user_id):return ('gigbid',user_id,'edit_counts')

    def record_approved_edit(self,user_id:str,before:str,after:str)->list[str]:
        matched=[]
        with self.lock:
            for signal,detector in STYLE_SIGNALS.items():
                if not detector(before,after):continue
                previous=self.store.get(self._edits_namespace(user_id),signal)
                count=int(previous.value['count'])+1 if previous else 1
                self.store.put(self._edits_namespace(user_id),signal,{'count':count},index=False)
                if count>=2:
                    self.store.put(self._memory_namespace(user_id),f'style:{signal}',
                                   {'category':'style','key':signal,'value':{'evidence_edits':count},'promoted':time.time()},index=False)
                    matched.append(signal)
        return matched

    def promote_outcome(self,user_id:str,job_category:str,outcome:str,source:str):
        if source!='marketplace_verified' or outcome not in ('replied','hired','lost'):
            raise ValueError('Unverified outcome cannot enter long-term memory')
        with self.lock:
            self.store.put(self._memory_namespace(user_id),f'outcome:{job_category}',
                {'category':'outcome','key':job_category,'value':{'outcome':outcome,'source':source},
                 'promoted':time.time()},index=False)

    def list(self,user_id:str):
        results=self.store.search(self._memory_namespace(user_id),limit=1000)
        return [{'id':memory_identifier(result.value['category'],result.value['key']),**result.value}
                for result in sorted(results,key=lambda item:item.value['promoted'],reverse=True)]

    def delete(self,user_id:str,memory_id:int)->bool:
        for item in self.list(user_id):
            if item['id']==memory_id:
                self.store.delete(self._memory_namespace(user_id),f"{item['category']}:{item['key']}")
                return True
        return False

    def style_instructions(self,user_id:str):
        return [item['key'] for item in self.list(user_id) if item['category']=='style']
