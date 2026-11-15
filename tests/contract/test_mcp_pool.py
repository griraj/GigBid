import sqlite3
import sys
from pathlib import Path
import pytest
from mcp import StdioServerParameters
from agent.mcp_pool import SessionWorker,close_workers
from agent.mcp_client import MCPRouter
from agent.tracing import trace_id


def test_same_process_serves_multiple_requests_and_recovers_after_timeout():
    worker=SessionWorker(StdioServerParameters(command=sys.executable,
        args=[str(Path(__file__).resolve().parents[1]/'fixtures/mcp_process.py')]))
    try:
        first=worker.call('process',{},15,{})
        second=worker.call('process',{},15,{})
        assert first.structuredContent==second.structuredContent
        with pytest.raises(TimeoutError):worker.call('process',{'delay':1},.1,{})
        recovered=worker.call('process',{},15,{})
        assert recovered.structuredContent!=first.structuredContent
    finally:
        worker.close();worker.thread.join(timeout=5)


def test_trace_metadata_is_per_request_on_shared_marketplace_session(tmp_path,monkeypatch):
    monkeypatch.setenv('GIGBID_DATA_DIR',str(tmp_path))
    monkeypatch.delenv('GIGBID_DB_PATH',raising=False)
    monkeypatch.setenv('GIGBID_MCP_PERSISTENT','1')
    router=MCPRouter()
    reset=trace_id.set('trace-first')
    try:
        for name in ('first','second'):
            trace_id.set('trace-'+name)
            router.call('approval','marketplace','send_message',{
                'job_id':'j100','body':'Thank you; please confirm the scope.',
                'idempotency_key':'trace-test-'+name,'dry_run':False})
        with sqlite3.connect(tmp_path/'gigbid.sqlite') as db:
            assert [row[0] for row in db.execute('select trace_id from audit order by id')]==['trace-first','trace-second']
    finally:
        trace_id.reset(reset);close_workers()
