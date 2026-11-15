"""Execute an honest open-model proposal comparison (requires Ollama).

Input JSONL: {"job":{...},"evidence":[{...}],"persona":"ai"}
Results are only produced after successful model calls; no fabricated scores.
"""
import argparse,json,time,os
from datetime import datetime,timezone
from pathlib import Path
from statistics import mean
import numpy as np
from agent.llm import draft_details_with_ollama
from agent.schemas import ProposalDraft
from rag.verify import verify

def compare(items,models):
    results={}
    for model in models:
        rows=[]
        print('Evaluating '+model,flush=True)
        for item in items:
            start=time.perf_counter()
            response=draft_details_with_ollama(item['job'],item['evidence'],model)
            raw=response['text']
            elapsed=time.perf_counter()-start
            cleaned,rejected=verify(ProposalDraft(text=raw,claim_evidence={}),item['evidence'])
            rows.append({'latency_s':elapsed,'removed_claims':len(rejected),
                         'before_chars':len(raw),'after_chars':len(cleaned),
                         'job_id':item['job']['id'],'raw':raw,'cleaned':cleaned,
                         'raw_model_response':response.get('raw_response'),
                         'done_reason':response['done_reason'],
                         'tokens':response['eval_count'],'prompt_tokens':response['prompt_eval_count'],
                         'tokens_per_second':response['eval_count']/(response['eval_duration']/1e9) if response.get('eval_duration') else None})
            print(f"{model} {item['job']['id']}: {elapsed:.2f}s, {response['eval_count']} generated tokens",flush=True)
        results[model]={'samples':len(rows),'p50_latency_s':round(float(np.percentile([r['latency_s'] for r in rows],50)),3),
                        'p95_latency_s':round(float(np.percentile([r['latency_s'] for r in rows],95)),3),
                        'verifier_rejections_per_proposal':round(mean(r['removed_claims'] for r in rows),3),
                        'characters_retained_ratio':round(mean(r['after_chars']/max(1,r['before_chars']) for r in rows),3),
                        'api_cost_usd':0,'model_provider':'local Ollama; hardware cost not included',
                        'generated_tokens':sum(r['tokens'] or 0 for r in rows),'rows':rows}
    return results

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--models',nargs='+',default=['qwen3:4b','qwen3:8b'])
    parser.add_argument('--output',type=Path,default=Path('evals/results/open_model_comparison.json'))
    parser.add_argument('--limit',type=int,default=None)
    parser.add_argument('--max-output-tokens',type=int,default=180)
    args=parser.parse_args()
    with args.input.open(encoding='utf-8') as file:items=[json.loads(line) for line in file if line.strip()]
    if not items:parser.error('Provide at least one labelled sample')
    if args.limit is not None:
        if args.limit<1:parser.error('--limit must be positive')
        items=items[:args.limit]
    if args.max_output_tokens<1:parser.error('--max-output-tokens must be positive')
    os.environ['GIGBID_MAX_OUTPUT_TOKENS']=str(args.max_output_tokens)
    summary={'metadata':{'created_at':datetime.now(timezone.utc).isoformat(),'corpus':str(args.input),
                         'max_output_tokens':args.max_output_tokens,
                         'writer_design':'writer_v2 structured fields and evidence IDs; factual sentences assembled from selected items',
                         'limitations':'Small synthetic writer smoke comparison; capped outputs may be incomplete proposals. Verifier rejection is not a calibrated unsupported-claim label. No reply/hire rates.'},
             'models':compare(items,args.models)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
