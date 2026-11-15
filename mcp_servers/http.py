"""Authenticated Portfolio MCP over Streamable HTTP.

Run: uvicorn mcp_servers.http:app --host 0.0.0.0 --port 8001
One private reviewer identity; this is not multi-tenant OAuth.
"""
import os
import secrets
import threading
import time
from collections import deque

from starlette.responses import JSONResponse
from mcp_servers.portfolio.server import mcp
from mcp.server.transport_security import TransportSecuritySettings

mcp.settings.stateless_http = True
mcp.settings.json_response = True
mcp.settings.host = '0.0.0.0'
mcp.settings.transport_security = TransportSecuritySettings(
    enable_dns_rebinding_protection=True,
    allowed_hosts=os.getenv('GIGBID_MCP_ALLOWED_HOSTS', 'localhost,localhost:*,127.0.0.1:*').split(','),
    allowed_origins=os.getenv('GIGBID_MCP_ALLOWED_ORIGINS', 'http://localhost:*,http://127.0.0.1:*').split(','),
)
inner = mcp.streamable_http_app()


class BearerGate:
    def __init__(self, app, token=None, requests_per_minute=None):
        self.app = app
        self.token = token if token is not None else os.getenv('GIGBID_MCP_BEARER', '')
        if self.token in ('', 'change-this-too', 'demo-reviewer-token'):
            raise RuntimeError('Set a private GIGBID_MCP_BEARER before exposing MCP HTTP')
        self.limit = requests_per_minute or int(os.getenv('GIGBID_MCP_RATE_LIMIT', '60'))
        if self.limit < 1:
            raise ValueError('MCP rate limit must be positive')
        self.calls = deque()
        self.lock = threading.Lock()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        supplied = headers.get(b'authorization', b'').decode('latin-1')
        if not secrets.compare_digest(supplied, 'Bearer ' + self.token):
            return await JSONResponse({'detail': 'Bearer token required'}, 401,
                                      headers={'WWW-Authenticate': 'Bearer'})(scope, receive, send)
        now = time.monotonic()
        with self.lock:
            while self.calls and self.calls[0] <= now - 60:
                self.calls.popleft()
            limited = len(self.calls) >= self.limit
            if not limited:
                self.calls.append(now)
        if limited:
            return await JSONResponse({'detail': 'Rate limit exceeded'}, 429,
                                      headers={'Retry-After': '60'})(scope, receive, send)
        return await self.app(scope, receive, send)


app = BearerGate(inner)
