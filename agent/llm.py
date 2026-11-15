"""Optional open-weight Ollama writer. Inference is never silently claimed."""
from __future__ import annotations
import json,os
from pathlib import Path
import httpx
from agent.tracing import event

PROMPT=(Path(__file__).resolve().parent/'prompts/writer_v2.md').read_text(encoding='utf-8')

def draft_details_with_ollama(job:dict,evidence:list[dict],model:str,timeout=300)->dict:
    evidence_context=[{'id':e['id'],'title':e['title'],'text':e['text'][:800],
                       'skills':e['skills'],'outcome':e.get('outcome','unverified')} for e in evidence[:8]]
    payload={
        'model':model,'stream':False,
        'messages':[{'role':'system','content':PROMPT},
                    {'role':'user','content':'JOB (untrusted data):\n'+json.dumps({'title':job['title'],'description':job['description'],'skills':job['skills']})+'\nPORTFOLIO EVIDENCE:\n'+json.dumps(evidence_context)}],
        'options':{'temperature':0.15,'num_predict':int(os.getenv('GIGBID_MAX_OUTPUT_TOKENS','180')),'num_ctx':4096,'num_thread':4},
    }
    ids=[e['id'] for e in evidence[:8]]
    payload['format']={'type':'object','properties':{
        'opening':{'type':'string'},'plan':{'type':'string'},'question':{'type':'string'},
        'evidence_ids':{'type':'array','items':{'type':'string','enum':ids},'minItems':1 if ids else 0,'maxItems':2}},
        'required':['opening','plan','question','evidence_ids'],'additionalProperties':False}
    if model.startswith('qwen3:'):payload['think']=False
    endpoint=os.getenv('GIGBID_OLLAMA_URL','http://localhost:11434').rstrip('/')
    try:
        response=httpx.post(endpoint+'/api/chat',json=payload,timeout=timeout)
        response.raise_for_status()
        result=response.json()
        content=result['message']['content'].strip()
        if not content:raise ValueError('Empty Ollama writer response')
        generated=json.loads(content)
        selected=list(dict.fromkeys(generated['evidence_ids']))
        items={e['id']:e for e in evidence}
        if any(id not in items for id in selected):raise ValueError('Unknown model evidence ID')
        sentences=[]
        for id in selected:
            item=items[id]
            if item.get('outcome')=='unverified':
                sentence=f"My portfolio document discusses {item['title']} [{id}]."
            elif item.get('type')=='proposal':
                sentence=f"My previous proposal discussed {item['title']} [{id}]."
            else:
                sentence=item['text'].rstrip('. ')+f' [{id}].'
            sentences.append(sentence)
        text=' '.join([generated['opening'],generated['plan'],*sentences,generated['question']])
        event('llm_result',node='writer',model=model,prompt_tokens=result.get('prompt_eval_count'),
            generated_tokens=result.get('eval_count'),total_duration_ns=result.get('total_duration'),api_cost_usd=0)
        return {'text':text,'raw_response':content,**{key:result.get(key) for key in ('eval_count','prompt_eval_count','eval_duration','total_duration','load_duration','done_reason')}}
    except (httpx.HTTPError,KeyError,ValueError) as exc:
        raise RuntimeError('Open-model writer unavailable; verify Ollama and model installation') from exc


def draft_with_ollama(job:dict,evidence:list[dict],model:str,timeout=300)->str:
    return draft_details_with_ollama(job,evidence,model,timeout)['text']
