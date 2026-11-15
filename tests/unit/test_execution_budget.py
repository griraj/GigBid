from uuid import uuid4
from langgraph.checkpoint.memory import MemorySaver
from agent.graphs.bid_graph import build_bid_graph


def test_token_estimate_blocks_before_marketplace_tools(monkeypatch):
    monkeypatch.setenv('GIGBID_TOOL_BACKEND','direct')
    class Marketplace:
        def get_client_history(self,*args):raise AssertionError('Should not be called')
    class Index:
        def search(self,*args,**kwargs):raise AssertionError('Should not be called')
    graph=build_bid_graph(Marketplace(),Index(),{'max_tokens':10},MemorySaver())
    job={'id':'job-test','title':'Large task','description':'Long text '*200,
         'skills':['Python'],'min_budget':10,'max_budget':50,'client_id':'c1','connects':5}
    state=graph.invoke({'job':job,'persona':'ai'},
        {'configurable':{'thread_id':uuid4().hex}})
    assert state['status']=='needs_attention'
    assert not state['budget']['allowed']
    assert 'draft' not in state
