"""Run one real local open-profile graph through API and MCP; never approve it."""
import json
import os
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


if __name__=='__main__':
    os.environ.update(GIGBID_DATA_DIR=str(ROOT/'tmp/open-profile'),
        GIGBID_LLM_BACKEND='ollama',GIGBID_RAG_BACKEND='ollama-vector',
        GIGBID_TOOL_BACKEND='mcp',GIGBID_MCP_TIMEOUT='120',GIGBID_MODE='local',
        GIGBID_API_TOKEN='open-profile-local-test',GIGBID_ENV='development')
    from fastapi.testclient import TestClient
    from apps.api.main import app
    started=time.perf_counter()
    with TestClient(app) as client:
        response=client.post('/runs',headers={'Authorization':'Bearer open-profile-local-test'},
            json={'job_id':'j100','persona':'ai'})
        response.raise_for_status()
        state=response.json()
    result={'source':'one synthetic local open-profile integration check, not a dev-set benchmark',
        'status':state['status'],'pending_approval':state.get('pending_approval',False),
        'evidence_ids':[item['id'] for item in state.get('evidence',[])],
        'draft':state.get('draft'),'latency_s':time.perf_counter()-started,
        'trace_id':response.headers.get('X-Trace-ID'),'approved':False}
    (ROOT/'evals/results/open_profile_integration.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    if state['status']=='submitted':raise RuntimeError('Unexpected unapproved send')
    print(json.dumps(result,indent=2))
