from agent.paths import marketplace_path
from agent.runs import RunRegistry


def test_data_directory_and_override(tmp_path, monkeypatch):
    monkeypatch.setenv('GIGBID_DATA_DIR', str(tmp_path))
    monkeypatch.delenv('GIGBID_DB_PATH', raising=False)
    assert marketplace_path() == str(tmp_path / 'gigbid.sqlite')
    monkeypatch.setenv('GIGBID_DB_PATH', str(tmp_path / 'custom.sqlite'))
    assert marketplace_path() == str(tmp_path / 'custom.sqlite')


def test_registry_survives_new_connection(tmp_path):
    path = tmp_path / 'runs.sqlite'
    first = RunRegistry(path)
    first.add('ai:j100:test', 'bid')
    second = RunRegistry(path)
    assert second.list('bid')[0][0] == 'ai:j100:test'
    assert second.list('conversation') == []
