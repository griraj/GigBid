"""Execute an honest open-model proposal comparison (requires Ollama).

Input JSONL: {"job":{...},"evidence":[{...}],"persona":"ai"}
Results are only produced after successful model calls; no fabricated scores.
"""
import argparse,json,time
from datetime import datetime,timezone
from pathlib import Path
from statistics import mean
import numpy as np
from agent.llm import draft_with_ollama
from agent.schemas import ProposalDraft
from rag.verify import verify

def compare(items,models):
    results={}
    for model in models:
        rows=[]
        for item in items:
            start=time.perf_counter()
            raw=draft_with_ollama(item['job'],item['evidence'],model)
            elapsed=time.perf_counter()-start
            cleaned,rejected=verify(ProposalDraft(text=raw,claim_evidence={}),item['evidence'])
            rows.append({'latency_s':elapsed,'removed_claims':len(rejected),
                         'before_chars':len(raw),'after_chars':len(cleaned)})
        results[model]={'samples':len(rows),'p50_latency_s':round(float(np.percentile([r['latency_s'] for r in rows],50)),3),
                        'p95_latency_s':round(float(np.percentile([r['latency_s'] for r in rows],95)),3),
                        'unsupported_claims_before_per_proposal':round(mean(r['removed_claims'] for r in rows),3),
                        'characters_retained_ratio':round(mean(r['after_chars']/max(1,r['before_chars']) for r in rows),3),
                        'api_cost_usd':0,'model_provider':'local Ollama; hardware cost not included'}
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--models',nargs='+',default=['qwen3:4b','qwen3:8b'])
    parser.add_argument('--output',type=Path,default=Path('evals/results/open_model_comparison.json'))
    args=parser.parse_args()
    with args.input.open(encoding='utf-8') as file:items=[json.loads(line) for line in file if line.strip()]
    if not items:parser.error('Provide at least one labelled sample')
    summary={'metadata':{'created_at':datetime.now(timezone.utc).isoformat(),'corpus':str(args.input),
                         'limitations':'Length, grounding and latency are not reply-rate or calibrated quality scores'},
             'models':compare(items,args.models)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
