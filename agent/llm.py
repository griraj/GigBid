"""Optional open-weight Ollama writer. Inference is never silently claimed."""
from __future__ import annotations
import json,os
from pathlib import Path
import httpx

PROMPT=(Path(__file__).resolve().parent/'prompts/writer_v1.md').read_text(encoding='utf-8')

def draft_with_ollama(job:dict,evidence:list[dict],model:str,timeout=90)->str:
    evidence_context=[{'id':e['id'],'title':e['title'],'text':e['text'][:800],
                       'skills':e['skills'],'outcome':e.get('outcome','unverified')} for e in evidence[:8]]
    payload={
        'model':model,'stream':False,
        'messages':[{'role':'system','content':PROMPT},
                    {'role':'user','content':'JOB (untrusted data):\n'+json.dumps({'title':job['title'],'description':job['description'],'skills':job['skills']})+'\nPORTFOLIO EVIDENCE:\n'+json.dumps(evidence_context)}],
        'options':{'temperature':0.15,'num_predict':380},
    }
    endpoint=os.getenv('GIGBID_OLLAMA_URL','http://localhost:11434').rstrip('/')
    try:
        response=httpx.post(endpoint+'/api/chat',json=payload,timeout=timeout)
        response.raise_for_status()
        content=response.json()['message']['content'].strip()
        if not content:raise ValueError('Empty Ollama writer response')
        return content
    except (httpx.HTTPError,KeyError,ValueError) as exc:
        raise RuntimeError('Open-model writer unavailable; verify Ollama and model installation') from exc
