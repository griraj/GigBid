"""Persistent, rule-gated SQLite memory; never promote raw tool output.

Development persistence only. Production should scope users with trusted
identity and use a LangGraph Postgres Store.
"""
import json,sqlite3,time
from pathlib import Path

STYLE_SIGNALS={
    'omit_greeting':lambda before,after:before.lower().lstrip().startswith(('hello','hi ')) and not after.lower().lstrip().startswith(('hello','hi ')),
    'avoid_passionate':lambda before,after:'passionate' in before.lower() and 'passionate' not in after.lower(),
    'prefer_brief':lambda before,after:len(after)<len(before)*0.75 and len(before)>80,
}

class MemoryStore:
    def __init__(self,path:Path|str):
        self.db=sqlite3.connect(str(path),check_same_thread=False)
        with self.db:
            self.db.execute('create table if not exists edits (id integer primary key, user_id text, signal text, original_length int, edited_length int, created real)')
            self.db.execute('create table if not exists memory (id integer primary key, user_id text, category text, key text, value text, promoted real, unique(user_id,category,key))')

    def record_approved_edit(self,user_id:str,before:str,after:str)->list[str]:
        """A style preference is promoted only after >=2 distinct approved edits."""
        matched=[]
        for signal,detector in STYLE_SIGNALS.items():
            if not detector(before,after):continue
            with self.db:
                self.db.execute('insert into edits(user_id,signal,original_length,edited_length,created) values(?,?,?,?,?)',
                                (user_id,signal,len(before),len(after),time.time()))
                count=self.db.execute('select count(*) from edits where user_id=? and signal=?',(user_id,signal)).fetchone()[0]
                if count>=2:
                    self.db.execute("insert into memory(user_id,category,key,value,promoted) values(?,?,?,?,?) on conflict(user_id,category,key) do update set value=excluded.value,promoted=excluded.promoted",
                                    (user_id,'style',signal,json.dumps({'evidence_edits':count}),time.time()))
                    matched.append(signal)
        return matched

    def promote_outcome(self,user_id:str,job_category:str,outcome:str,source:str):
        """Only independently confirmed marketplace outcomes can be promoted."""
        if source!='marketplace_verified' or outcome not in ('replied','hired','lost'):
            raise ValueError('Unverified outcome cannot enter long-term memory')
        with self.db:
            self.db.execute("insert into memory(user_id,category,key,value,promoted) values(?,?,?,?,?) on conflict(user_id,category,key) do update set value=excluded.value,promoted=excluded.promoted",
                (user_id,'outcome',job_category,json.dumps({'outcome':outcome,'source':source}),time.time()))

    def list(self,user_id:str):
        return [dict(id=id,category=category,key=key,value=json.loads(value),promoted=promoted)
                for id,category,key,value,promoted in self.db.execute('select id,category,key,value,promoted from memory where user_id=? order by promoted desc',(user_id,))]

    def delete(self,user_id:str,memory_id:int)->bool:
        with self.db:cursor=self.db.execute('delete from memory where user_id=? and id=?',(user_id,memory_id))
        return cursor.rowcount>0

    def style_instructions(self,user_id:str):
        return [item['key'] for item in self.list(user_id) if item['category']=='style']
