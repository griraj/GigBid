import pytest
from agent.memory.store import MemoryStore

def test_style_promotes_only_after_multiple_approved_edits(tmp_path):
    m=MemoryStore(tmp_path/'mem.sqlite')
    assert m.record_approved_edit('reviewer','Hello, I can do the work.','I can do the work.')==[]
    assert m.list('reviewer')==[]
    assert m.record_approved_edit('reviewer','Hello, this is a relevant project.','This is a relevant project.')==['omit_greeting']
    items=m.list('reviewer')
    assert len(items)==1
    assert m.delete('reviewer',items[0]['id'])
    assert m.list('reviewer')==[]

def test_outcome_needs_verified_source(tmp_path):
    m=MemoryStore(tmp_path/'mem.sqlite')
    with pytest.raises(ValueError):m.promote_outcome('reviewer','ai','hired','user_guess')
    m.promote_outcome('reviewer','ai','replied','marketplace_verified')
    assert m.list('reviewer')[0]['value']['outcome']=='replied'
