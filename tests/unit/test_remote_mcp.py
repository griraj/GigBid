import pytest
from agent.remote_mcp import github_client,upwork_client

def test_remote_connectors_fail_closed_without_authorization(monkeypatch):
    monkeypatch.delenv('GIGBID_GITHUB_TOKEN',raising=False)
    monkeypatch.delenv('GIGBID_UPWORK_OAUTH_BEARER',raising=False)
    with pytest.raises(RuntimeError,match='GitHub integration disabled'):github_client()
    with pytest.raises(RuntimeError,match='Upwork live mode unavailable'):upwork_client()
