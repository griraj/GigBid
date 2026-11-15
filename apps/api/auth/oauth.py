"""Per-account encrypted provider tokens and one-use OAuth state challenges."""
from __future__ import annotations

import os
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from cryptography.fernet import Fernet


class OAuthVault:
    def __init__(self,path:Path|str,key:str|bytes):
        if not key:raise ValueError('Set GIGBID_OAUTH_ENCRYPTION_KEY to a Fernet key')
        self.cipher=Fernet(key.encode() if isinstance(key,str) else key)
        self.lock=threading.RLock()
        self.db=sqlite3.connect(str(path),check_same_thread=False)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS oauth_tokens (user_id TEXT NOT NULL, provider TEXT NOT NULL, ciphertext BLOB NOT NULL, updated REAL NOT NULL, PRIMARY KEY(user_id,provider))')
            self.db.execute('CREATE TABLE IF NOT EXISTS oauth_states (nonce TEXT PRIMARY KEY, user_id TEXT NOT NULL, provider TEXT NOT NULL, expires REAL NOT NULL)')

    def begin(self,user_id:str,provider:str,ttl:int=600)->str:
        nonce=secrets.token_urlsafe(32)
        with self.lock,self.db:
            self.db.execute('INSERT INTO oauth_states VALUES (?,?,?,?)',(nonce,user_id,provider,time.time()+ttl))
        return nonce

    def consume(self,nonce:str,provider:str)->str|None:
        with self.lock,self.db:
            row=self.db.execute('SELECT user_id, expires FROM oauth_states WHERE nonce=? AND provider=?',(nonce,provider)).fetchone()
            self.db.execute('DELETE FROM oauth_states WHERE nonce=?',(nonce,))
        return row[0] if row and row[1]>time.time() else None

    def save(self,user_id:str,provider:str,token:str)->None:
        with self.lock,self.db:
            self.db.execute('INSERT INTO oauth_tokens VALUES (?,?,?,?) ON CONFLICT(user_id,provider) DO UPDATE SET ciphertext=excluded.ciphertext,updated=excluded.updated',
                            (user_id,provider,self.cipher.encrypt(token.encode()),time.time()))

    def load(self,user_id:str,provider:str)->str|None:
        with self.lock:
            row=self.db.execute('SELECT ciphertext FROM oauth_tokens WHERE user_id=? AND provider=?',(user_id,provider)).fetchone()
        return self.cipher.decrypt(row[0]).decode() if row else None

    def connected(self,user_id:str)->list[str]:
        with self.lock:
            return [row[0] for row in self.db.execute('SELECT provider FROM oauth_tokens WHERE user_id=?',(user_id,))]

    def disconnect(self,user_id:str,provider:str)->bool:
        with self.lock,self.db:
            return self.db.execute('DELETE FROM oauth_tokens WHERE user_id=? AND provider=?',(user_id,provider)).rowcount>0


def from_environment(path:Path|str)->OAuthVault:
    return OAuthVault(path,os.getenv('GIGBID_OAUTH_ENCRYPTION_KEY',''))
