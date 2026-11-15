"""Compare fresh versus reused real MCP transports on identical synthetic flows."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def child(mode):
    os.environ.update(GIGBID_MCP_PERSISTENT=mode,GIGBID_TOOL_BACKEND='mcp',
        GIGBID_MODE='local',GIGBID_RAG_BACKEND='lexical',GIGBID_LLM_BACKEND='template',
        GIGBID_ENV='development',GIGBID_API_TOKEN='local-benchmark-only',
        GIGBID_DATA_DIR=str(ROOT/'tmp'/('benchmark-'+mode+'-'+str(time.time_ns()))))
    os.environ.pop('GIGBID_DB_PATH',None)
    from fastapi.testclient import TestClient
    from apps.api.main import app
    from agent.mcp_pool import close_workers
    rows=[]
    try:
        with TestClient(app) as client:
            headers={'Authorization':'Bearer local-benchmark-only'}
            for iteration in range(2):
                start=time.perf_counter()
                response=client.post('/runs',headers=headers,json={'job_id':'j100','persona':'ai'})
                response.raise_for_status();state=response.json()
                analysis=time.perf_counter()-start
                start=time.perf_counter()
                approved=client.post('/runs/'+state['thread_id']+'/approval',headers=headers,json={'action':'approve'})
                approved.raise_for_status()
                rows.append({'iteration':iteration+1,'analysis_s':analysis,'approval_s':time.perf_counter()-start,
                    'status':approved.json()['status']})
    finally:close_workers()
    return rows


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--child',choices=['0','1'])
    args=parser.parse_args()
    if args.child:print(json.dumps(child(args.child)))
    else:
        result={'scope':'local HTTP test client, real stdio MCP; synthetic template/lexical flow; no hosted latency inference'}
        for mode,label in [('0','fresh_sessions'),('1','persistent_sessions')]:
            process=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child',mode],
                cwd=ROOT,capture_output=True,text=True,check=True)
            result[label]=json.loads(process.stdout.strip().splitlines()[-1])
            print(label+': '+json.dumps(result[label]),flush=True)
        path=ROOT/'evals/results/mcp_performance.json'
        path.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
