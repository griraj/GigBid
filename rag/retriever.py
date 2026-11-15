"""Five reproducible retrieval configurations, without fabricated embeddings.

CPU sparse vectors are explicitly a fallback; V0 is TF-IDF, not neural dense.
"""
from __future__ import annotations
import math
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def terms(s: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:[.+#-][a-z0-9]+)*", s.lower())

class EvidenceIndex:
    def __init__(self, items):
        self.items = list(items)
        self.texts = [i['title']+' '+i['text']+' '+' '.join(i['skills']) for i in self.items]
        self.vectorizer = TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(self.texts)
        self.tokens = [terms(t) for t in self.texts]
        self.df = {w:sum(w in ts for ts in self.tokens) for w in set().union(*(set(t) for t in self.tokens))}

    def _dense(self, query):
        return cosine_similarity(self.vectorizer.transform([query]), self.matrix)[0]

    def _bm25(self, query):
        q = terms(query)
        avg = sum(map(len,self.tokens))/max(len(self.tokens),1)
        scores=[]
        for ts in self.tokens:
            score=0.0
            for w in q:
                f=ts.count(w)
                if not f: continue
                idf=math.log(1+(len(self.tokens)-self.df[w]+0.5)/(self.df[w]+0.5))
                score += idf*f*2.2/(f+1.2*(0.25+0.75*len(ts)/avg))
            scores.append(score)
        return np.array(scores)

    def search(self, query, k=5, variant='v2', requirements=None, persona=None):
        if variant=='v8':
            from rag.corrective_graph import run_corrective
            return run_corrective(self,query,requirements,persona,k)
        allowed=np.array([persona is None or x['persona']==persona for x in self.items])
        dense=self._dense(query)
        if variant == 'v0': scores=dense
        elif variant == 'v1':
            qs=requirements or [query]
            scores=np.zeros(len(self.items))
            for q in qs: scores=np.maximum(scores,self._dense(q))
        else:
            bm=self._bm25(query)
            rank_d=np.argsort(-dense); rank_b=np.argsort(-bm)
            scores=np.zeros(len(self.items))
            for rank,idx in enumerate(rank_d): scores[idx]+=1/(60+rank+1)
            for rank,idx in enumerate(rank_b): scores[idx]+=1/(60+rank+1)
            if variant=='v3':
                query_set=set(terms(query))
                scores+=np.array([len(query_set & set(t))/max(1,len(query_set))*0.025 for t in self.tokens])
            if variant=='v4':
                scores+=np.array([0.015 if x['outcome'] in ('won','positive_review') else 0 for x in self.items])
        scores=np.where(allowed,scores,-float('inf'))
        indices=np.argsort(-scores)[:k]
        return [{**self.items[i], 'retrieval_score':float(scores[i])} for i in indices if np.isfinite(scores[i]) and scores[i]>0]
