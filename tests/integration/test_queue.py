from fastapi.testclient import TestClient
from apps.api.main import app


client=TestClient(app)
HEADERS={'Authorization':'Bearer demo-reviewer-token'}


def test_worker_queue_requires_durable_services(monkeypatch):
    monkeypatch.delenv('GIGBID_REDIS_URL',raising=False)
    monkeypatch.delenv('GIGBID_CHECKPOINT_DATABASE_URL',raising=False)
    response=client.post('/runs/queue',headers=HEADERS,json={'job_id':'j100','persona':'ai'})
    assert response.status_code==503


def test_queue_does_not_run_graph_in_request(monkeypatch):
    import arq.connections
    monkeypatch.setenv('GIGBID_REDIS_URL','redis://localhost:6379/0')
    monkeypatch.setenv('GIGBID_CHECKPOINT_DATABASE_URL','postgresql://example')
    class FakeJob:
        job_id='queued-job'
    class FakePool:
        async def enqueue_job(self,*args,**kwargs):
            assert args[0]=='analyze_job'
            assert kwargs['_job_id'].startswith('gigbid:analysis:')
            return FakeJob()
        async def aclose(self):pass
    async def fake_pool(settings):return FakePool()
    monkeypatch.setattr(arq.connections,'create_pool',fake_pool)
    response=client.post('/runs/queue',headers=HEADERS,json={'job_id':'j100','persona':'ai'})
    assert response.status_code==202,response.text
    queued=response.json()
    assert queued['status']=='queued'
    assert client.get('/runs/'+queued['thread_id'],headers=HEADERS).json()['status']=='queued'
