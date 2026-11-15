"""Narrow synchronous bridge to the official MCP ClientSession over stdio.

Each node is granted only named tools. No graph node imports an MCP server
implementation or reads its underlying database. Synchronous graph calls reuse
server sessions; GIGBID_MCP_PERSISTENT=0 retains the fresh-session baseline.
"""
from __future__ import annotations
import asyncio,json,os,sys
from pathlib import Path
from agent.paths import marketplace_path
from agent.tracing import trace_id,event
import time

ROOT=Path(__file__).resolve().parents[1]

ALLOWLIST={
    'scout':{'marketplace':{'search_jobs','get_job'}},
    'risk':{'marketplace':{'get_client_history'}},
    'fit':{'portfolio':{'search_evidence','get_case_study','list_skills'}},
    'pricing':{'marketplace':{'get_client_history','get_connects_balance'}},
    'writer':{'portfolio':{'search_evidence','get_case_study'}},
    'critic':{'portfolio':{'get_case_study'}},
    'liaison':{'marketplace':{'list_messages','send_message'},'workspace':{'free_calendar_slots','create_interview_hold','create_email_draft'}},
    'approval':{'marketplace':{'create_proposal_draft','submit_proposal','send_message'}},
}

class MCPUnavailable(RuntimeError):pass
class MCPPermissionDenied(PermissionError):pass

class MCPRouter:
    def __init__(self,timeout:float=25):self.timeout=float(os.getenv('GIGBID_MCP_TIMEOUT',str(timeout)))

    async def acall(self,role:str,server:str,name:str,arguments:dict|None=None):
        if name not in ALLOWLIST.get(role,{}).get(server,set()):
            raise MCPPermissionDenied(f'{role} is not authorized to invoke {server}.{name}')
        from mcp import ClientSession,StdioServerParameters
        from mcp.client.stdio import stdio_client
        if server not in ('marketplace','portfolio','workspace'):raise MCPPermissionDenied('Unknown MCP server')
        params=StdioServerParameters(command=sys.executable,
               args=['-m',f'mcp_servers.{server}.server'],
               env={**os.environ,'GIGBID_DB_PATH':marketplace_path(),'GIGBID_TRACE_ID':trace_id.get(),
                    'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
        try:
            started=time.perf_counter()
            event('mcp_call',role=role,server=server,tool=name,arguments=arguments or {})
            async def execute():
                async with stdio_client(params) as (read,write):
                    async with ClientSession(read,write) as session:
                        await session.initialize()
                        result=await session.call_tool(name,arguments or {})
                        event('mcp_result',server=server,tool=name,is_error=result.isError,latency_ms=(time.perf_counter()-started)*1000)
                        if result.isError:raise MCPUnavailable(f'{server}.{name} failed: {result.content}')
                        structured=result.structuredContent
                        if isinstance(structured,dict):
                            if set(structured)=={'result'}:return structured['result']
                            return structured
                        for block in result.content:
                            if block.type=='text':
                                try:return json.loads(block.text)
                                except json.JSONDecodeError:return block.text
                        return None
            return await asyncio.wait_for(execute(),self.timeout)
        except (TimeoutError,OSError,ExceptionGroup) as exc:
            raise MCPUnavailable(f'{server}.{name} is unavailable: {type(exc).__name__}') from exc

    def call(self,role:str,server:str,name:str,arguments:dict|None=None):
        # Graph nodes and FastAPI routes are synchronous; never nest this in
        # an event-loop thread. FastAPI runs ordinary def routes in workers.
        if os.getenv('GIGBID_MCP_PERSISTENT','1')=='0':
            return asyncio.run(self.acall(role,server,name,arguments))
        if name not in ALLOWLIST.get(role,{}).get(server,set()):
            raise MCPPermissionDenied(f'{role} is not authorized to invoke {server}.{name}')
        if server not in ('marketplace','portfolio','workspace'):raise MCPPermissionDenied('Unknown MCP server')
        from mcp import StdioServerParameters
        from agent.mcp_pool import get_worker
        params=StdioServerParameters(command=sys.executable,args=['-m',f'mcp_servers.{server}.server'],
            env={**os.environ,'GIGBID_DB_PATH':marketplace_path(),'GIGBID_TRACE_ID':'',
                 'PYTHONPATH':str(ROOT)+os.pathsep+os.environ.get('PYTHONPATH','')})
        started=time.perf_counter()
        event('mcp_call',role=role,server=server,tool=name,arguments=arguments or {})
        try:
            result=get_worker(params).call(name,arguments or {},self.timeout,{'trace_id':trace_id.get()})
        except (TimeoutError,OSError,RuntimeError) as exc:
            raise MCPUnavailable(f'{server}.{name} unavailable; request was not automatically retried') from exc
        event('mcp_result',server=server,tool=name,is_error=result.isError,latency_ms=(time.perf_counter()-started)*1000)
        if result.isError:raise MCPUnavailable(f'{server}.{name} failed')
        if isinstance(result.structuredContent,dict):
            structured=result.structuredContent
            return structured['result'] if set(structured)=={'result'} else structured
        for block in result.content:
            if block.type=='text':
                try:return json.loads(block.text)
                except json.JSONDecodeError:return block.text
        return None
