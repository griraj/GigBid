"""Durable saved search schedules with per-user deduplication."""
from __future__ import annotations

import sqlite3
import threading
import time
from uuid import uuid4


class SavedSearches:
    def __init__(self,path):
        self.lock=threading.RLock()
        self.db=sqlite3.connect(str(path),check_same_thread=False,timeout=30)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS saved_searches (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, query TEXT NOT NULL, persona TEXT NOT NULL, interval_hours INTEGER NOT NULL, last_run REAL NOT NULL DEFAULT 0)')
            self.db.execute('CREATE TABLE IF NOT EXISTS seen_jobs (search_id TEXT NOT NULL, job_id TEXT NOT NULL, PRIMARY KEY(search_id,job_id))')

    def add(self,owner_id:str,query:str,persona:str,interval_hours:int=4):
        if not 4<=interval_hours<=168:raise ValueError('Search interval must be 4 to 168 hours')
        if persona not in ('ai','web','analytics'):raise ValueError('Unknown persona')
        if not query.strip() or len(query)>200:raise ValueError('Search query must be 1 to 200 characters')
        key=uuid4().hex
        with self.lock,self.db:
            self.db.execute('INSERT INTO saved_searches VALUES (?,?,?,?,?,0)',(key,owner_id,query.strip(),persona,interval_hours))
        return {'id':key,'query':query.strip(),'persona':persona,'interval_hours':interval_hours}

    def list(self,owner_id:str):
        with self.lock:
            rows=self.db.execute('SELECT id,query,persona,interval_hours,last_run FROM saved_searches WHERE owner_id=?',(owner_id,)).fetchall()
        return [dict(id=key,query=query,persona=persona,interval_hours=hours,last_run=last)
                for key,query,persona,hours,last in rows]

    def due(self,now=None):
        now=now or time.time()
        with self.lock:
            rows=self.db.execute('SELECT id,owner_id,query,persona,interval_hours FROM saved_searches WHERE last_run + interval_hours * 3600 <= ?', (now,)).fetchall()
        return [dict(id=key,owner_id=owner,query=query,persona=persona,interval_hours=hours)
                for key,owner,query,persona,hours in rows]

    def seen(self,search_id:str,job_id:str)->bool:
        with self.lock:
            return self.db.execute('SELECT 1 FROM seen_jobs WHERE search_id=? AND job_id=?',(search_id,job_id)).fetchone() is not None

    def mark_seen(self,search_id:str,job_id:str):
        with self.lock,self.db:
            self.db.execute('INSERT OR IGNORE INTO seen_jobs VALUES (?,?)',(search_id,job_id))

    def mark_run(self,search_id:str,now=None):
        with self.lock,self.db:
            self.db.execute('UPDATE saved_searches SET last_run=? WHERE id=?',(now or time.time(),search_id))

    def delete(self,owner_id:str,search_id:str)->bool:
        with self.lock,self.db:
            deleted=self.db.execute('DELETE FROM saved_searches WHERE id=? AND owner_id=?',(search_id,owner_id)).rowcount
            if deleted:self.db.execute('DELETE FROM seen_jobs WHERE search_id=?',(search_id,))
            return bool(deleted)
