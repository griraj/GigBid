import json
from pathlib import Path
from scripts.snapshot_tools import schemas


def test_mcp_signatures_match_reviewed_snapshot():
    expected=json.loads(Path(__file__).with_name('tool_schema_snapshot.json').read_text())
    assert schemas()==expected,'Review intentional schema changes, then run scripts/snapshot_tools.py'
