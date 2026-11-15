import pytest
from agent.mcp_client import MCPRouter,MCPPermissionDenied
from mcp_servers.marketplace.server import mcp as marketplace_mcp
from mcp_servers.portfolio.server import mcp as portfolio_mcp
from mcp_servers.workspace.server import mcp as workspace_mcp

def test_marketplace_schema_and_annotations():
    tools={tool.name:tool for tool in marketplace_mcp._tool_manager.list_tools()}
    assert set(tools)=={'search_jobs','get_job','get_client_history','get_connects_balance','list_messages',
                         'create_proposal_draft','submit_proposal','send_message'}
    for name,tool in tools.items():
        assert tool.annotations is not None
        if name in ('create_proposal_draft','submit_proposal','send_message'):
            assert tool.annotations.readOnlyHint is False
            assert tool.annotations.idempotentHint is True
            assert 'idempotency_key' in tool.parameters['properties']
            assert 'dry_run' in tool.parameters['properties']
        else:assert tool.annotations.readOnlyHint is True

def test_portfolio_and_workspace_names():
    assert {'search_evidence','list_skills','get_case_study'}=={t.name for t in portfolio_mcp._tool_manager.list_tools()}
    assert {'free_calendar_slots','create_interview_hold','create_email_draft'}=={t.name for t in workspace_mcp._tool_manager.list_tools()}

def test_role_allowlist_rejects_write_before_network_call():
    with pytest.raises(MCPPermissionDenied):
        MCPRouter().call('fit','marketplace','submit_proposal',{'job_id':'j100'})

def test_read_mcp_transport_roundtrip():
    result=MCPRouter().call('risk','marketplace','get_client_history',{'client_id':'c1'})
    assert result['payment_verified'] is True
