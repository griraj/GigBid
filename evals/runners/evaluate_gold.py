"""Run retrieval variants against independent human-labelled evidence IDs.

JSONL input: {"query":"...","persona":"ai","requirements":["python"],
              "relevant_evidence_ids":["portfolio-..."],"job_type":"data"}
No labels -> no score. Never use source records as their own ground truth.
"""
from __future__ import annotations
import argparse,json,math,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from data.synthetic import EVIDENCE
from rag.ingest_portfolio import load_portfolio
from rag.retriever import EvidenceIndex
from rag.neural import NeuralEvidenceIndex

def grade(index,labels,variants):
    results={}
    for variant in variants:
        rows=[]
        for label in labels:
            relevant=set(label['relevant_evidence_ids'])
            if not relevant:continue
            start=time.perf_counter()
            hits=index.search(label['query'],k=10,variant=variant,
                persona=label['persona'],requirements=label.get('requirements'))
            latency=(time.perf_counter()-start)*1000
            ids=[e['id'] for e in hits]
            precision=len(set(ids[:5]) & relevant)/max(1,min(5,len(ids)))
            recall=len(set(ids[:5]) & relevant)/len(relevant)
            rank=next((i+1 for i,id in enumerate(ids) if id in relevant),None)
            dcg=sum(1/math.log2(i+2) for i,id in enumerate(ids) if id in relevant)
            ideal=sum(1/math.log2(i+2) for i in range(min(len(relevant),10)))
            rows.append({'precision_at_5':precision,'recall_at_5':recall,'mrr':1/rank if rank else 0,
                         'ndcg_at_10':dcg/ideal,'latency_ms':latency,
                         'persona':label['persona'],'job_type':label.get('job_type','unspecified')})
        if not rows:raise ValueError('No nonempty gold evidence sets; cannot compute retrieval metrics')
        metrics={key:round(float(np.mean([r[key] for r in rows])),4) for key in
                 ('precision_at_5','recall_at_5','mrr','ndcg_at_10')}
        metrics['p95_latency_ms']=round(float(np.percentile([r['latency_ms'] for r in rows],95)),3)
        metrics['evaluated_queries']=len(rows)
        metrics['by_persona']={p:round(float(np.mean([r['recall_at_5'] for r in rows if r['persona']==p])),4)
                               for p in sorted({r['persona'] for r in rows})}
        metrics['by_job_type']={p:round(float(np.mean([r['recall_at_5'] for r in rows if r['job_type']==p])),4)
                               for p in sorted({r['job_type'] for r in rows})}
        results[variant]=metrics
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--labels',type=Path,required=True)
    parser.add_argument('--backend',choices=['lexical','neural'],default='lexical')
    parser.add_argument('--output',type=Path,default=Path('evals/results/gold_retrieval.json'))
    parser.add_argument('--model',default='sentence-transformers/all-MiniLM-L6-v2')
    args=parser.parse_args()
    with args.labels.open(encoding='utf-8') as stream:labels=[json.loads(line) for line in stream if line.strip()]
    if not labels:parser.error('No labels provided')
    evidence=EVIDENCE+load_portfolio()
    index=EvidenceIndex(evidence) if args.backend=='lexical' else NeuralEvidenceIndex(evidence,model_name=args.model)
    variants=['v0','v1','v2','v3','v4','v8']
    results={'metadata':{'source_labels':str(args.labels),'backend':args.backend,'model':args.model if args.backend=='neural' else 'TF-IDF',
                         'evaluated_at':datetime.now(timezone.utc).isoformat(),
                         'note':'Human-labelled relevance only; no GigSim reply/hire outcomes'},
             'variants':grade(index,labels,variants)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,indent=2)+'\n')
    print(json.dumps(results,indent=2))
