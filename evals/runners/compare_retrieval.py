"""Measured comparisons on tiny synthetic fixtures, never represented as instructor dev scores."""
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from statistics import median
from data.synthetic import EVIDENCE,JOBS,GOLD
from rag.retriever import EvidenceIndex

def evaluate():
    index=EvidenceIndex(EVIDENCE)
    results={'metadata':{'source':'hand-labelled synthetic fixtures, NOT GigSim or Kaggle','jobs':len(GOLD),'evidence_items':len(EVIDENCE),'timestamp':datetime.now(timezone.utc).isoformat(),'embedding':'TF-IDF lexical vectors (no neural model)','limitations':'Small, authored corpus; not representative of real recall or model performance'},'variants':{}}
    for variant in ['v0','v1','v2','v3','v4','v8']:
        recalls=[];precisions=[];f1s=[];mrrs=[];ndcgs=[];latencies=[];per_persona={}
        for j in JOBS:
            gold=GOLD[j['id']];target=set(gold['evidence'])
            if not target:continue
            q=j['title']+' '+j['description'];start=time.perf_counter()
            hits=index.search(q,k=10,variant=variant,requirements=j['skills'],persona=gold['persona'])
            latencies.append((time.perf_counter()-start)*1000)
            ids=[h['id'] for h in hits];top5=set(ids[:5]);rec=len(target&top5)/len(target)
            precision=len(target&top5)/max(1,len(ids[:5]))
            precisions.append(precision)
            f1s.append(2*precision*rec/(precision+rec) if precision+rec else 0)
            rank=next((i+1 for i,eid in enumerate(ids) if eid in target),None)
            mrr=1/rank if rank else 0
            import math
            dcg=sum(1/math.log2(i+2) for i,eid in enumerate(ids) if eid in target)
            ideal=sum(1/math.log2(i+2) for i in range(min(len(target),10)))
            ndcg=dcg/ideal if ideal else 0
            recalls.append(rec);mrrs.append(mrr);ndcgs.append(ndcg)
            per_persona.setdefault(gold['persona'],[]).append(rec)
        import numpy as np
        results['variants'][variant]={'recall_at_5':round(float(np.mean(recalls)),4),'mrr':round(float(np.mean(mrrs)),4),'ndcg_at_10':round(float(np.mean(ndcgs)),4),'latency_p50_ms':round(float(np.percentile(latencies,50)),3),'latency_p95_ms':round(float(np.percentile(latencies,95)),3),'recall_at_5_by_persona':{p:round(sum(vals)/len(vals),4) for p,vals in per_persona.items()}}
        results['variants'][variant].update(precision_at_5=round(float(np.mean(precisions)),4),
            f1_at_5=round(float(np.mean(f1s)),4),evaluated_queries=len(recalls))
    return results

if __name__=='__main__':
    result=evaluate();path=Path(__file__).resolve().parents[1]/'results'/'synthetic_retrieval.json';path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
