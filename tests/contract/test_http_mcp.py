import importlib
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


def test_mcp_http_auth_and_rate_limit(monkeypatch):
    monkeypatch.setenv('GIGBID_MCP_BEARER', 'test-private-token-123')
    module = importlib.import_module('mcp_servers.http')
    async def ok(request):
        return JSONResponse({'ok': True})
    wrapped = module.BearerGate(Starlette(routes=[Route('/', ok)]),
                                token='test-private-token-123', requests_per_minute=1)
    with TestClient(wrapped) as client:
        assert client.get('/').status_code == 401
        headers = {'Authorization': 'Bearer test-private-token-123'}
        assert client.get('/', headers=headers).status_code == 200
        assert client.get('/', headers=headers).status_code == 429
        assert client.get('/').status_code == 401


def test_real_mcp_http_initialize(monkeypatch):
    monkeypatch.setenv('GIGBID_MCP_BEARER', 'test-private-token-123')
    module = importlib.import_module('mcp_servers.http')
    with TestClient(module.app, base_url='http://localhost') as client:
        response = client.post('/mcp', headers={
            'Authorization': 'Bearer test-private-token-123',
            'Accept': 'application/json, text/event-stream',
        }, json={'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
            'protocolVersion': '2025-03-26', 'capabilities': {},
            'clientInfo': {'name': 'contract-test', 'version': '1'},
        }})
        assert response.status_code == 200, response.text
        assert response.json()['result']['serverInfo']['name'] == 'GigBid Evidence Vault'
