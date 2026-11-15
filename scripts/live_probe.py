"""Time an explicitly authorised synthetic review flow. Token comes only from stdin."""
import argparse,json,sys,time,getpass
from pathlib import Path
import httpx


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='https://gigbid-ti71.onrender.com')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print('Reviewer token on stdin (never stored):',flush=True)
    token=getpass.getpass('Private reviewer token: ').strip()
    if not token:raise SystemExit('A private token is required')
    with httpx.Client(base_url=args.url.rstrip('/')+'/api',headers={'Authorization':'Bearer '+token},timeout=180) as client:
        del token
        health=client.get('/health');health.raise_for_status()
        if health.json().get('mode')!='local':raise SystemExit('Probe only supports the synthetic local marketplace')
        result={'url':args.url,'scope':'authorised synthetic local job; real HTTP and MCP timing','health':health.json()}
        start=time.perf_counter();jobs=client.get('/jobs');jobs.raise_for_status()
        result['jobs_seconds']=time.perf_counter()-start
        nodes=[];state=None;event='';start=time.perf_counter()
        with client.stream('POST','/runs/stream',json={'job_id':'j100','persona':'ai'}) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line.startswith('event: '):event=line[7:]
                if line.startswith('data: '):
                    data=json.loads(line[6:])
                    if event=='node':nodes.append({'node':data['node'],'elapsed_s':time.perf_counter()-start})
                    elif event=='done':state=data
                    elif event=='error':raise RuntimeError(data.get('detail','Analysis failed'))
        result['analysis_seconds']=time.perf_counter()-start;result['nodes']=nodes
        if not state:raise RuntimeError('Stream ended without completed state')
        result['analysis_status']=state['status']
        if state.get('pending_approval'):
            start=time.perf_counter()
            approved=client.post('/runs/'+state['thread_id']+'/approval',json={'action':'approve'})
            approved.raise_for_status()
            result['approval_seconds']=time.perf_counter()-start
            result['approval_status']=approved.json()['status']
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
