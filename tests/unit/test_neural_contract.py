"""Adapter contract verified without pretending these test vectors are a real model."""
import numpy as np
from rag.neural import NeuralEvidenceIndex

class FakeEmbedder:
    def encode(self,inputs,**kwargs):
        return np.array([[1,0] if 'python' in s.lower() else [0,1] for s in inputs],dtype=float)

class FakeCollection:
    def __init__(self):self.records={}
    def get(self,include):return {'ids':list(self.records),'metadatas':[v[2] for v in self.records.values()]}
    def upsert(self,ids,embeddings,documents,metadatas):
        for id,vector,doc,meta in zip(ids,embeddings,documents,metadatas):self.records[id]=(vector,doc,meta)
    def delete(self,ids):
        for id in ids:self.records.pop(id,None)
    def query(self,query_embeddings,n_results,include,where=None):
        hits=[]
        for id,(vector,doc,metadata) in self.records.items():
            if where and metadata['persona']!=where['persona']:continue
            distance=1-np.dot(query_embeddings[0],vector)
            hits.append((id,float(distance)))
        hits.sort(key=lambda pair:pair[1])
        hits=hits[:n_results]
        return {'ids':[[id for id,_ in hits]],'distances':[[d for _,d in hits]]}

class FakeClient:
    def __init__(self):self.collection=FakeCollection()
    def get_or_create_collection(self,name):return self.collection

def test_neural_contract_updates_and_filters():
    evidence=[{'id':'p1','persona':'ai','type':'case_study','title':'Python model','text':'Python classification project','skills':['python'],'outcome':'delivered'},
              {'id':'p2','persona':'web','type':'case_study','title':'React app','text':'React dashboard','skills':['react'],'outcome':'delivered'}]
    client=FakeClient();idx=NeuralEvidenceIndex(evidence,embedder=FakeEmbedder(),store=client)
    assert idx.search('python',k=2,variant='v0',persona='ai')[0]['id']=='p1'
    assert idx.search('python',k=2,variant='v0',persona='web')[0]['id']=='p2'
    NeuralEvidenceIndex(evidence[:1],embedder=FakeEmbedder(),store=client)
    assert set(client.collection.records)=={'p1'}
