from langgraph.checkpoint.memory import MemorySaver
from agent.graphs.bid_graph import build_bid_graph
from agent.marketplace_port import LocalMarketplace
from data.synthetic import JOBS,EVIDENCE
from rag.retriever import EvidenceIndex


def test_truncated_model_draft_is_blocked_before_approval(monkeypatch):
    monkeypatch.setenv('GIGBID_TOOL_BACKEND','direct')
    monkeypatch.setenv('GIGBID_LLM_BACKEND','ollama')
    monkeypatch.setattr('agent.llm.draft_details_with_ollama',lambda *args,**kwargs:{
        'text':'I delivered retention modelling [e1]. '*4,'eval_count':180,'done_reason':'length'})
    marketplace=LocalMarketplace(':memory:')
    try:
        graph=build_bid_graph(marketplace,EvidenceIndex(EVIDENCE),
            {'models':{'open':{'writer':'test'}},'max_critic_revisions':2},MemorySaver())
        state=graph.invoke({'job':JOBS[0],'persona':'ai','revision':0},
            {'configurable':{'thread_id':'truncated'}})
        assert state['status']=='blocked'
        assert any('truncated' in reason for reason in state['compliance']['reasons'])
        assert marketplace.db.execute('select count(*) from writes').fetchone()[0]==0
    finally:marketplace.db.close()
