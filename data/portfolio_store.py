"""Tenant-owned portfolio uploads, stored separately from authored demo data."""
import sqlite3
import threading
import time
from uuid import uuid4


class PortfolioStore:
    def __init__(self,path):
        self.lock=threading.RLock()
        self.db=sqlite3.connect(str(path),check_same_thread=False)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS portfolio_uploads (id TEXT PRIMARY KEY, owner_id TEXT NOT NULL, filename TEXT NOT NULL, text TEXT NOT NULL, created REAL NOT NULL)')

    def add(self,owner_id:str,filename:str,text:str)->dict:
        if not text.strip():raise ValueError('Document contains no extractable text')
        if len(text)>300000:raise ValueError('Document text exceeds limit')
        item_id='upload_'+uuid4().hex
        created=time.time()
        with self.lock,self.db:
            self.db.execute('INSERT INTO portfolio_uploads VALUES (?,?,?,?,?)',(item_id,owner_id,filename,text,created))
        return {'id':item_id,'filename':filename,'chars':len(text),'created':created,'source':'user_uploaded'}

    def list(self,owner_id:str)->list[dict]:
        with self.lock:
            rows=self.db.execute('SELECT id,filename,text,created FROM portfolio_uploads WHERE owner_id=? ORDER BY created DESC',(owner_id,)).fetchall()
        return [{'id':item_id,'filename':filename,'text':body,'created':created,'source':'user_uploaded'}
                for item_id,filename,body,created in rows]

    def delete(self,owner_id:str,item_id:str)->bool:
        with self.lock,self.db:
            return self.db.execute('DELETE FROM portfolio_uploads WHERE id=? AND owner_id=?',(item_id,owner_id)).rowcount>0
