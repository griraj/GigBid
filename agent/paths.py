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


def tenant_marketplace_path(owner_id: str) -> str:
    """One isolated local-simulator database per authenticated account.

    The reviewer fixture retains its original database. Tenant IDs originate
    from server-generated UUIDs, never from user-controlled path segments.
    """
    if os.getenv('GIGBID_AUTH_MODE','reviewer') != 'multi' or owner_id == 'reviewer':
        return marketplace_path()
    import re
    if not re.fullmatch(r'[0-9a-f]{32}', owner_id):
        raise ValueError('Invalid tenant identifier')
    directory=data_path('tenants')
    directory.mkdir(parents=True,exist_ok=True)
    return str(directory / f'{owner_id}.sqlite')
