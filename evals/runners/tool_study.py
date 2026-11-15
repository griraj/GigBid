"""Run the 40-task tool-granularity study with a real local Ollama model.

Task labels are authored synthetic probes, NOT the instructor's GigSim labels.
The script refuses to write results if model calls fail; raw predictions and
token usage are kept to make every aggregate reproducible.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from statistics import mean
import httpx

ROOT=Path(__file__).resolve().parents[2]
SCHEMAS=json.loads((ROOT/'tests/contract/tool_schema_snapshot.json').read_text())

# These labels are fixed by the action requested, not generated from a model.
PROBES=[
 ('marketplace','search_jobs',{'query':'python'},'Find Python contract opportunities'),
 ('marketplace','get_job',{'job_id':'j100'},'Open the full listing j100'),
 ('marketplace','get_client_history',{'client_id':'c100'},'Check client c100 payment and hire history'),
 ('marketplace','get_connects_balance',{},'How many Connects remain?'),
 ('marketplace','list_messages',{'job_id':'j100'},'Read the messages for job j100'),
 ('marketplace','create_proposal_draft',{'job_id':'j100','text':'I can help with this Python task.','idempotency_key':'task-probe-001','dry_run':True},'Preview an unsent proposal draft for j100'),
 ('marketplace','submit_proposal',{'job_id':'j100','text':'I can help with this Python task.','idempotency_key':'task-probe-002','dry_run':True},'Preview the final submission and Connects cost for j100'),
 ('marketplace','send_message',{'job_id':'j100','body':'Thank you for the clarification.','idempotency_key':'task-probe-003','dry_run':True},'Preview a reply to client on j100'),
 ('portfolio','search_evidence',{'requirement':'python','persona':'ai','k':5},'Find evidence of Python experience for the AI persona'),
 ('portfolio','get_case_study',{'id':'e1'},'Open portfolio case study e1'),
 ('portfolio','list_skills',{'persona':'ai'},'List the AI persona portfolio skills'),
 ('workspace','free_calendar_slots',{'days':7},'Find free interview slots over the next seven days'),
 ('workspace','create_interview_hold',{'slot':'2026-11-20T10:00:00+00:00','job_id':'j100'},'Create a tentative interview hold for j100'),
 ('workspace','create_email_draft',{'subject':'Interview','body':'Please confirm a suitable time.'},'Prepare an email draft without sending it'),
]

DESCRIPTIONS={
 'search_jobs':'Search marketplace jobs by query','get_job':'Read one complete job by job_id',
 'get_client_history':'Retrieve a client history by client_id',
 'get_connects_balance':'Read remaining bidding Connects',
 'list_messages':'Read messages from a job conversation',
 'create_proposal_draft':'Create a proposal draft, not submit it',
 'submit_proposal':'Submit a proposal after approval; spend Connects',
 'send_message':'Send a client message after approval',
 'search_evidence':'Retrieve portfolio evidence for a skill requirement',
 'get_case_study':'Get an evidence case study by id',
 'list_skills':'List demonstrated portfolio skills',
 'free_calendar_slots':'Read free interview slots',
 'create_interview_hold':'Hold an interview time tentatively',
 'create_email_draft':'Create email draft only; do not send',
}

def labelled_tasks():
    tasks=[]
    for variation in ('Please ', 'I need you to ', 'Which tool should I use to '):
        for server,tool,args,request in PROBES:
            tasks.append({'request':variation+request[0].lower()+request[1:],
                          'server':server,'tool':tool,'arguments':args})
    return tasks[:40]

def tool_catalog(variant):
    groups={}
    for server,tools in SCHEMAS.items():
        for name,schema in tools.items():
            group=f'{server}_{"write" if schema["annotations"].get("readOnlyHint") is False else "read"}'
            groups[f'{server}.{name}']=group
    if variant=='coarse':
        return [{'name':name,'description':f'{name.replace("_"," ")} operation category'}
                for name in sorted(set(groups.values()))],groups
    return [{'name':f'{server}.{name}',
             'description':DESCRIPTIONS[name]+(' Use exact identifiers; never perform writes without approval.' if variant=='rewritten' else ''),
             'required_arguments':schema['parameters'].get('required',[])}
            for server,tools in SCHEMAS.items() for name,schema in tools.items()],groups

def run(model,limit=40,base_url=None):
    tasks=labelled_tasks()[:limit]
    base_url=(base_url or os.getenv('GIGBID_OLLAMA_URL','http://localhost:11434')).rstrip('/')
    results={}
    with httpx.Client(timeout=120) as client:
        for variant in ('fine','coarse','rewritten'):
            catalog,groups=tool_catalog(variant)
            rows=[]
            for task in tasks:
                prompt=('Choose exactly one of these tool names for the request. Return JSON with keys '
                        '"name" and "arguments". Never call a tool.\nTOOLS: '+json.dumps(catalog)+
                        '\nREQUEST: '+task['request'])
                started=time.perf_counter()
                response=client.post(base_url+'/api/generate',json={'model':model,'prompt':prompt,
                         'stream':False,'format':'json','options':{'temperature':0}})
                response.raise_for_status()
                data=response.json()
                prediction=json.loads(data['response'])
                expected=groups[f"{task['server']}.{task['tool']}"] if variant=='coarse' else f"{task['server']}.{task['tool']}"
                actual=prediction.get('name')
                predicted_args=prediction.get('arguments',{})
                correct_args=isinstance(predicted_args,dict) and all(
                    str(predicted_args.get(k))==str(v) for k,v in task['arguments'].items())
                rows.append({'request':task['request'],'expected_tool':expected,'predicted_tool':actual,
                    'expected_arguments':task['arguments'],'predicted_arguments':predicted_args,
                    'tool_correct':actual==expected,'arguments_correct':correct_args,
                    'prompt_tokens':data.get('prompt_eval_count'),'completion_tokens':data.get('eval_count'),
                    'latency_s':time.perf_counter()-started,'raw_response':data['response']})
            results[variant]={'tasks':len(rows),'tool_selection_accuracy':mean(int(r['tool_correct']) for r in rows),
                'argument_accuracy':mean(int(r['arguments_correct']) for r in rows),
                'mean_tokens_per_task':mean((r['prompt_tokens'] or 0)+(r['completion_tokens'] or 0) for r in rows),
                'rows':rows}
    return {'metadata':{'task_source':'authored synthetic tool probes (not instructor labels)',
            'model':model,'variants':list(results),'limitations':'Prompted model selection; tools were not executed. Coarse and fine name-space accuracies are not directly equivalent.'},'results':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--model',required=True)
    parser.add_argument('--limit',type=int,default=40)
    parser.add_argument('--output',type=Path,default=Path('evals/results/tool_study_ollama.json'))
    args=parser.parse_args()
    if not 1<=args.limit<=40:parser.error('--limit must be between 1 and 40')
    result=run(args.model,args.limit)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Wrote real model predictions to',args.output)
