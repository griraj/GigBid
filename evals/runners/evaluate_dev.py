"""Evaluate supplied development labels without approving any marketplace write.

Each JSONL line must contain job, persona, expected_bid, expected_scam,
relevant_evidence_ids; fair_price_band is optional [low, high].
The configured marketplace must contain the referenced clients/jobs because
MCP risk reads and dry-run previews use its actual contract.
"""
import argparse
import json
import time
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from evals.runners.evaluate_system import classification


def evaluate(labels):
    from apps.api.main import bid_graph,CONFIG,index
    rows=[]
    for position,label in enumerate(labels):
        started=time.perf_counter()
        job=label['job'];persona=label['persona']
        state=bid_graph.invoke({'job':job,'persona':persona,'revision':0},
            {'configurable':{'thread_id':f'dev:{time.time_ns()}:{position}'}})
        hits=index.search(job['title']+' '+job['description'],persona=persona,k=10,
            requirements=job['skills'],variant=CONFIG.get('rag_variant','v2'))
        ids=[item['id'] for item in hits];relevant=set(label['relevant_evidence_ids'])
        band=label.get('fair_price_band');price=state.get('price',{}).get('amount')
        rows.append({'job_id':job['id'],'persona':persona,'expected_bid':bool(label['expected_bid']),
            'predicted_bid':state['decision']['action']=='bid','expected_scam':bool(label['expected_scam']),
            'predicted_scam':state['risk']['score']>=0.55,
            'evidence_recall_at_5':len(set(ids[:5])&relevant)/len(relevant) if relevant else None,
            'price_in_band':band[0]<=price<=band[1] if band and price is not None else None,
            'verifier_rejections':len(state.get('draft',{}).get('removed_claims',[])),
            'latency_s':time.perf_counter()-started,'status':state['status']})
    def summary(group):
        prices=[r['price_in_band'] for r in group if r['price_in_band'] is not None]
        recalls=[r['evidence_recall_at_5'] for r in group if r['evidence_recall_at_5'] is not None]
        return {'jobs':len(group),
            'decision':classification([r['predicted_bid'] for r in group],[r['expected_bid'] for r in group]),
            'scam':classification([r['predicted_scam'] for r in group],[r['expected_scam'] for r in group]),
            'evidence_recall_at_5':float(np.mean(recalls)) if recalls else None,
            'price_in_band_rate':float(np.mean(prices)) if prices else None,
            'priced_jobs':len(prices),'p50_latency_s':float(np.percentile([r['latency_s'] for r in group],50)),
            'p95_latency_s':float(np.percentile([r['latency_s'] for r in group],95))}
    return {'overall':summary(rows),'by_persona':{p:summary([r for r in rows if r['persona']==p]) for p in sorted({r['persona'] for r in rows})},'rows':rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--labels',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path('evals/results/dev_system.json'))
    args=parser.parse_args()
    labels=[json.loads(line) for line in args.labels.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not labels:parser.error('No development labels supplied')
    result={'metadata':{'source':str(args.labels),'timestamp':datetime.now(timezone.utc).isoformat(),
        'notes':'Watch counts as non-bid; no approval resumed; no reply/hire outcomes inferred'},**evaluate(labels)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['overall'],indent=2))
