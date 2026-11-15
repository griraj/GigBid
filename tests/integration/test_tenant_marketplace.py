from fastapi.testclient import TestClient
from apps.api.main import app,accounts
from agent.marketplace_port import local_tenant_marketplace
from agent.paths import tenant_marketplace_path
from agent.mcp_client import MCPRouter
from data.portfolio_store import PortfolioStore
from uuid import uuid4


client=TestClient(app)


def test_two_accounts_have_separate_connects_and_messages(monkeypatch,tmp_path):
    monkeypatch.setenv('GIGBID_AUTH_MODE','multi')
    monkeypatch.setenv('GIGBID_MODE','local')
    monkeypatch.setenv('GIGBID_DATA_DIR',str(tmp_path))
    nonce=uuid4().hex
    alice=accounts.register(f'alice-{nonce}@example.test','private-long-passphrase-a')
    bob=accounts.register(f'bob-{nonce}@example.test','private-long-passphrase-b')
    alice_port=local_tenant_marketplace(alice['id'])
    bob_port=local_tenant_marketplace(bob['id'])
    assert alice_port.get_connects_balance()==100
    assert bob_port.get_connects_balance()==100
    alice_port.send_message('j100','Thanks, I can discuss scope.','tenant-message-key-a')
    assert len(alice_port.list_messages('j100'))==1
    assert bob_port.list_messages('j100')==[]
    alice_port.submit_proposal('j100','Please review this evidence-backed proposal.','tenant-proposal-a')
    assert bob_port.get_connects_balance()==100
    assert alice_port.get_connects_balance()<100
    assert tenant_marketplace_path(alice['id'])!=tenant_marketplace_path(bob['id'])


def test_portfolio_mcp_search_filters_user_documents(monkeypatch,tmp_path):
    monkeypatch.setenv('GIGBID_AUTH_MODE','multi')
    monkeypatch.setenv('GIGBID_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('GIGBID_MCP_PERSISTENT','0')
    alice=uuid4().hex;bob=uuid4().hex
    PortfolioStore(tmp_path/'portfolio_uploads.sqlite').add(alice,'spectrograph.md',
        'Spectrograph pipeline built for astronomical spectrum processing.')
    router=MCPRouter()
    alice_hits=router.call('fit','portfolio','search_evidence',
        {'requirement':'spectrograph astronomical','persona':'ai'},owner_id=alice)
    bob_hits=router.call('fit','portfolio','search_evidence',
        {'requirement':'spectrograph astronomical','persona':'ai'},owner_id=bob)
    assert any(item['source']=='user_uploaded' for item in alice_hits)
    assert not any(item.get('source')=='user_uploaded' for item in bob_hits)
