"""Shared persistent paths for the API and its MCP child processes."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def data_path(filename: str) -> Path:
    directory = Path(os.getenv('GIGBID_DATA_DIR', str(ROOT / 'local_data')))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / filename


def marketplace_path() -> str:
    return os.getenv('GIGBID_DB_PATH', str(data_path('gigbid.sqlite')))
