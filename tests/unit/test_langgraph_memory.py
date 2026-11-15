import pytest
from langgraph.store.memory import InMemoryStore
from agent.memory.langgraph_store import LangGraphMemory


def test_outcomes_and_style_promote_only_when_verified():
    mem=LangGraphMemory(InMemoryStore())
    original='Hello, I am passionate about building suitable data visualizations for business dashboards.'
    changed='I build business dashboards.'
    assert mem.record_approved_edit('alice',original,changed)==[]
    assert mem.list('alice')==[]
    second=mem.record_approved_edit('alice',original,changed)
    assert 'prefer_brief' in second
    assert mem.list('bob')==[]
    with pytest.raises(ValueError):
        mem.promote_outcome('alice','ai','hired','unverified_log')
    mem.promote_outcome('alice','ai','replied','marketplace_verified')
    records=mem.list('alice')
    assert any(record['category']=='outcome' for record in records)
    assert mem.delete('alice',records[0]['id'])
    assert len(mem.list('alice'))==len(records)-1
