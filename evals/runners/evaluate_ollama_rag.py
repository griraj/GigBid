"""Real dense/hybrid comparisons on the same explicitly synthetic fixture."""
import json
from pathlib import Path
from datetime import datetime,timezone
from data.synthetic import JOBS,EVIDENCE,GOLD
from rag.ollama_vector import build_ollama_index
from evals.runners.evaluate_gold import grade


if __name__=='__main__':
    labels=[{'query':job['title']+' '+job['description'],'persona':GOLD[job['id']]['persona'],
        'requirements':job['skills'],'relevant_evidence_ids':GOLD[job['id']]['evidence'],
        'job_type':job['category']} for job in JOBS]
    index=build_ollama_index(EVIDENCE)
    variants={}
    for variant in ['v0','v1','v2','v4','v8']:
        index.embedder.cache.clear()
        variants.update(grade(index,labels,[variant]))
        print('Evaluated '+variant,flush=True)
    result={'metadata':{'timestamp':datetime.now(timezone.utc).isoformat(),
        'source':'authored synthetic fixtures, not instructor dev data',
        'embedding_model':'nomic-embed-text via local Ollama','vector_store':'SQLite with sqlite-vec cosine distance',
        'query_cache':'Cleared before each variant; indexing excluded; underlying model warmed by index preparation',
        'limitations':'Five positive queries; V3 excluded because cross-encoder weights are not installed'},
        'variants':variants}
    path=Path('evals/results/ollama_retrieval.json')
    path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
