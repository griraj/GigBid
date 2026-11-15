from worker.searches import SavedSearches
import pytest


def test_due_searches_owner_scoping_and_dedup(tmp_path):
    db=SavedSearches(tmp_path/'searches.sqlite')
    alice=db.add('alice','python','ai',4)
    bob=db.add('bob','react','web',8)
    assert [row['id'] for row in db.list('alice')]==[alice['id']]
    assert {row['id'] for row in db.due(now=200000)}=={alice['id'],bob['id']}
    db.mark_seen(alice['id'],'j100')
    db.mark_seen(alice['id'],'j100')
    assert db.seen(alice['id'],'j100')
    db.mark_run(alice['id'],now=200000)
    assert alice['id'] not in {row['id'] for row in db.due(now=201000)}
    assert not db.delete('bob',alice['id'])
    assert db.delete('alice',alice['id'])
    with pytest.raises(ValueError):db.add('alice','rapid','ai',1)
