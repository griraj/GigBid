"""Real open-model embeddings with a persistent Chroma vector store.

Neural mode fails explicitly when the model cannot be downloaded or loaded;
the lexical baseline is selectable separately, never mislabeled as neural.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np

DEFAULT_EMBEDDING='sentence-transformers/all-MiniLM-L6-v2'
DEFAULT_RERANKER='cross-encoder/ms-marco-MiniLM-L-6-v2'

class NeuralEvidenceIndex:
    def __init__(self,items,model_name=DEFAULT_EMBEDDING,directory='data/processed/chroma',reranker_name=DEFAULT_RERANKER,
                 embedder=None,store=None,reranker=None):
        if embedder is None:
            from sentence_transformers import SentenceTransformer
            embedder=SentenceTransformer(model_name,device='cpu')
        self.embedder=embedder
        self.reranker_name=reranker_name
        self.reranker=reranker
        self.items={e['id']:e for e in items}
        self.model_name=model_name
        if store is None:
            import chromadb
            store=chromadb.PersistentClient(path=str(directory))
        self.client=store
        self.collection=store.get_or_create_collection('gigbid_portfolio')
        self._sync()

    def _sync(self):
        """Incremental upsert for changed items; explicit deletion for missing items."""
        existing=self.collection.get(include=['metadatas'])
        known={id:(meta or {}).get('sha') for id,meta in zip(existing['ids'],existing['metadatas'] or [])}
        updates=[]
        for item in self.items.values():
            body=item['title']+'\n'+item['text']+'\nSkills: '+', '.join(item['skills'])
            checksum=hashlib.sha256((body+item['persona']).encode()).hexdigest()
            if known.get(item['id'])!=checksum:updates.append((item,body,checksum))
        if updates:
            vectors=self.embedder.encode([body for _,body,_ in updates],normalize_embeddings=True,convert_to_numpy=True)
            self.collection.upsert(ids=[e['id'] for e,_,_ in updates],embeddings=np.asarray(vectors,dtype=float).tolist(),
                documents=[body for _,body,_ in updates],metadatas=[{'persona':e['persona'],'sha':sha,'type':e['type']} for e,_,sha in updates])
        deleted=list(set(known)-set(self.items))
        if deleted:self.collection.delete(ids=deleted)

    def search(self,query,k=5,variant='v2',requirements=None,persona=None):
        from rag.retriever import EvidenceIndex
        if not self.items:return []
        # Candidate recall uses true neural cosine on normalized vectors.
        vectors=np.asarray(self.embedder.encode([query],normalize_embeddings=True,convert_to_numpy=True))
        kwargs={'query_embeddings':vectors.tolist(),'n_results':min(max(k*4,20),len(self.items)),
                'include':['distances']}
        if persona:kwargs['where']={'persona':persona}
        found=self.collection.query(**kwargs)
        ids=found['ids'][0];distances=found['distances'][0]
        neural={id:1.0-float(distance) for id,distance in zip(ids,distances)}
        if variant=='v0':return [{**self.items[id],'retrieval_score':neural[id]} for id in ids[:k]]
        if variant=='v1':
            all_queries=requirements or [query]
            for q in all_queries:
                qvec=np.asarray(self.embedder.encode([q],normalize_embeddings=True,convert_to_numpy=True))
                sub=self.collection.query(query_embeddings=qvec.tolist(),n_results=min(k*4,len(self.items)),
                      where={'persona':persona} if persona else None,include=['distances'])
                for id,d in zip(sub['ids'][0],sub['distances'][0]):neural[id]=max(neural.get(id,-1),1-float(d))
        # Reciprocal rank fusion of neural and lexical candidates, with optional cross-encoder reranking.
        lexical=EvidenceIndex([self.items[id] for id in self.items if persona is None or self.items[id]['persona']==persona])
        keyword=lexical.search(query,k=len(lexical.items),variant='v2',requirements=requirements,persona=persona)
        ranked_neural=sorted(neural,key=neural.get,reverse=True)
        combined={}
        for rank,id in enumerate(ranked_neural):combined[id]=combined.get(id,0)+1/(60+rank+1)
        for rank,e in enumerate(keyword):combined[e['id']]=combined.get(e['id'],0)+1/(60+rank+1)
        ids=sorted(combined,key=combined.get,reverse=True)
        if variant=='v4':ids=sorted(ids,key=lambda id:combined[id]+(0.005 if self.items[id].get('outcome') in ('won','positive_review') else 0),reverse=True)
        if variant=='v3':
            if self.reranker is None:
                from sentence_transformers import CrossEncoder
                self.reranker=CrossEncoder(self.reranker_name,device='cpu')
            rerank_ids=ids[:min(30,len(ids))]
            scores=self.reranker.predict([(query,self.items[id]['text']) for id in rerank_ids])
            ids=sorted(zip(rerank_ids,scores),key=lambda pair:float(pair[1]),reverse=True)
            ids=[id for id,_ in ids]+ids[len(rerank_ids):]
        if variant=='v8' and (not ids or max(neural.values(),default=-1)<0.15):
            return self.search(' '.join(requirements or [query]),k,'v1',requirements,persona)
        return [{**self.items[id],'retrieval_score':float(combined[id])} for id in ids[:k]]
