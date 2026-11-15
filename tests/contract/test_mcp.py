from mcp_servers.portfolio.server import list_skills,get_case_study
from mcp_servers.workspace.server import free_calendar_slots

def test_portfolio_contract():
    assert 'python' in list_skills('ai')
    assert get_case_study('e1')['id']=='e1'

def test_workspace_contract():
    assert len(free_calendar_slots(7))<=7
