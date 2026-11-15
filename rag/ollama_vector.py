"""CPU-friendly real embeddings in a persistent SQLite/sqlite-vec vector store.

Uses the existing neural variant pipeline. V3 still requires the optional
SentenceTransformer cross-encoder; it never silently substitutes lexical scores.
"""
import json
import os
import sqlite3
import threading
from pathlib import Path
import httpx
import numpy as np


class OllamaEmbedder:
    def __init__(self,model='nomic-embed-text'):
        self.model=model
        self.cache={}

    def encode(self,texts,normalize_embeddings=True,convert_to_numpy=True):
        texts=list(texts)
        missing=list(dict.fromkeys(text for text in texts if text not in self.cache))
        if not missing:return np.asarray([self.cache[text] for text in texts],dtype=np.float32)
        endpoint=os.getenv('GIGBID_OLLAMA_URL','http://localhost:11434').rstrip('/')
        response=httpx.post(endpoint+'/api/embed',json={'model':self.model,'input':missing},timeout=300)
        response.raise_for_status()
        vectors=np.asarray(response.json()['embeddings'],dtype=np.float32)
        if normalize_embeddings:
            vectors=vectors/np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
        self.cache.update(zip(missing,vectors))
        return np.asarray([self.cache[text] for text in texts],dtype=np.float32)


class SQLiteVectorStore:
    def __init__(self,directory,model):
        import sqlite_vec
        Path(directory).mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(Path(directory)/'vectors.sqlite'),check_same_thread=False,timeout=30)
        self.lock=threading.RLock()
        self.db.enable_load_extension(True)
        sqlite_vec.load(self.db)
        self.db.enable_load_extension(False)
        with self.db:
            self.db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY,value TEXT)')
            self.db.execute('CREATE TABLE IF NOT EXISTS vectors (id TEXT PRIMARY KEY,vector BLOB,persona TEXT,metadata TEXT)')
            existing=self.db.execute("SELECT value FROM settings WHERE key='model'").fetchone()
            if existing and existing[0]!=model:
                raise ValueError('Embedding model changed; choose a new vector directory')
            self.db.execute("INSERT OR IGNORE INTO settings VALUES ('model',?)",(model,))

    def get_or_create_collection(self,name):return self

    def get(self,include=None):
        with self.lock:rows=self.db.execute('SELECT id,metadata FROM vectors').fetchall()
        return {'ids':[r[0] for r in rows],'metadatas':[json.loads(r[1]) for r in rows]}

    def upsert(self,ids,embeddings,documents,metadatas):
        with self.lock,self.db:
            for id,vector,metadata in zip(ids,embeddings,metadatas):
                self.db.execute('INSERT INTO vectors VALUES (?,?,?,?) ON CONFLICT(id) DO UPDATE SET vector=excluded.vector,persona=excluded.persona,metadata=excluded.metadata',
                    (id,np.asarray(vector,dtype=np.float32).tobytes(),metadata['persona'],json.dumps(metadata)))

    def delete(self,ids):
        with self.lock,self.db:self.db.executemany('DELETE FROM vectors WHERE id=?',[(id,) for id in ids])

    def query(self,query_embeddings,n_results,where=None,include=None):
        results=[];distances=[]
        for embedding in query_embeddings:
            sql='SELECT id,vec_distance_cosine(vector,?) AS distance FROM vectors'
            params=[np.asarray(embedding,dtype=np.float32).tobytes()]
            if where:
                sql+=' WHERE persona=?';params.append(where['persona'])
            sql+=' ORDER BY distance LIMIT ?';params.append(n_results)
            with self.lock:rows=self.db.execute(sql,params).fetchall()
            results.append([r[0] for r in rows]);distances.append([r[1] for r in rows])
        return {'ids':results,'distances':distances}


def build_ollama_index(items,directory=None,model=None):
    from agent.paths import data_path
    from rag.neural import NeuralEvidenceIndex
    model=model or os.getenv('GIGBID_OLLAMA_EMBEDDING_MODEL','nomic-embed-text')
    return NeuralEvidenceIndex(items,model_name=model,embedder=OllamaEmbedder(model),
        store=SQLiteVectorStore(directory or data_path('vectors'),model))
