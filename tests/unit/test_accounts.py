from apps.api.auth.accounts import Accounts, check_password, password_hash
from agent.runs import RunRegistry


def test_password_storage_uses_random_salt():
    first=password_hash('long-private-password')
    second=password_hash('long-private-password')
    assert first != second
    assert check_password('long-private-password',first)
    assert not check_password('wrong',first)


def test_sessions_are_scoped_and_expire(tmp_path):
    accounts=Accounts(tmp_path/'users.sqlite')
    alice=accounts.register('ALICE@example.com','long-private-password')
    bob=accounts.register('bob@example.com','another-long-password')
    assert alice['id']!=bob['id']
    assert accounts.login('alice@example.com','bad-password') is None
    session=accounts.login('alice@example.com','long-private-password')
    assert accounts.identity(session['access_token'])['id']==alice['id']
    assert session['access_token'] not in (tmp_path/'users.sqlite').read_bytes().decode('latin1')
    accounts.logout(session['access_token'])
    assert accounts.identity(session['access_token']) is None


def test_registry_tenant_filter_and_legacy_migration(tmp_path):
    registry=RunRegistry(tmp_path/'runs.sqlite')
    registry.add('thread-a','bid','alice')
    registry.add('thread-b','bid','bob')
    assert [row[0] for row in registry.list('bid',owner_id='alice')]==['thread-a']
    assert not registry.owns('thread-a','bob')
    assert registry.owns('thread-a','alice')
