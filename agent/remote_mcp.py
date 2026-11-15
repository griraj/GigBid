"""Explicitly authorized third-party MCP connectors.

No calls are made automatically. Upwork OAuth is an interactive host-level
flow and cannot be substituted with an API key or a scraped browser cookie.
"""
from __future__ import annotations
import os
from langchain_mcp_adapters.client import MultiServerMCPClient

UPWORK_URL='https://mcp.upwork.com/mcp'

def github_client():
    """Read-only GitHub MCP tool discovery via GitHub's official Docker server.

    Requires docker and a user-supplied minimally scoped token; the policy
    controls actual permissions, and this connector never calls write tools.
    """
    token=os.getenv('GIGBID_GITHUB_TOKEN')
    if not token:raise RuntimeError('GitHub integration disabled: no authorized read-only token')
    return MultiServerMCPClient({'github':{'transport':'stdio','command':'docker',
        'args':['run','-i','--rm','-e','GITHUB_PERSONAL_ACCESS_TOKEN',
                '-e','GITHUB_TOOLSETS=repos','-e','GITHUB_READ_ONLY=1',
                'ghcr.io/github/github-mcp-server'],
        'env':{'GITHUB_PERSONAL_ACCESS_TOKEN':token}}})

def upwork_client():
    """Fail closed without a host-verified user OAuth bearer token.

    This is a transport configurator, NOT a completed OAuth authorization
    flow or a promise that arbitrary hosted callback URLs are supported.
    """
    token=os.getenv('GIGBID_UPWORK_OAUTH_BEARER')
    if not token:raise RuntimeError('Upwork live mode unavailable until user OAuth authorization and approved callback')
    return MultiServerMCPClient({'upwork':{'transport':'streamable_http','url':UPWORK_URL,
        'headers':{'Authorization':f'Bearer {token}'}}})

async def github_read_tools():
    client=github_client()
    tools=await client.get_tools()
    return [tool for tool in tools if tool.name in ('get_file_contents','search_repositories','search_code','get_repository_tree')]
