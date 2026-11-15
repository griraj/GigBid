from agent.mcp_client import scoped_mcp_env


def test_mcp_env_does_not_expose_unrelated_oauth_credentials(monkeypatch):
    monkeypatch.setenv('GIGBID_GITHUB_OAUTH_CLIENT_SECRET','private-github-secret')
    monkeypatch.setenv('GIGBID_OAUTH_ENCRYPTION_KEY','private-fernet-key')
    monkeypatch.setenv('GIGBID_GIGSIM_TOKEN','private-simulator-token')
    monkeypatch.setenv('GIGBID_DATA_DIR','/tmp/gigbid-test-mcp')
    env=scoped_mcp_env('portfolio','reviewer')
    assert 'GIGBID_GITHUB_OAUTH_CLIENT_SECRET' not in env
    assert 'GIGBID_OAUTH_ENCRYPTION_KEY' not in env
    assert 'GIGBID_GIGSIM_TOKEN' not in env
    assert scoped_mcp_env('marketplace','reviewer')['GIGBID_GIGSIM_TOKEN']=='private-simulator-token'
