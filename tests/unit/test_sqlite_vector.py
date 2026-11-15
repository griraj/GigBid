import numpy as np
from rag.ollama_vector import SQLiteVectorStore


def test_persistent_cosine_query_and_persona_filter(tmp_path):
    store=SQLiteVectorStore(tmp_path,'test-embedding')
    store.upsert(['a','b'],[[1,0],[0,1]],['a','b'],
        [{'persona':'ai','sha':'a'},{'persona':'web','sha':'b'}])
    result=store.query([[1,0]],n_results=2,where={'persona':'ai'})
    assert result['ids']==[['a']]
    assert abs(result['distances'][0][0])<1e-6
    store.db.close()
    second=SQLiteVectorStore(tmp_path,'test-embedding')
    assert set(second.get()['ids'])=={'a','b'}
    second.delete(['a'])
    assert second.get()['ids']==['b']
    second.db.close()
