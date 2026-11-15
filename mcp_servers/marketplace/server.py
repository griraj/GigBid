import os
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field
from typing import Annotated
from agent.marketplace_port import build_marketplace

mcp=FastMCP('GigBid Marketplace Gateway')
port=build_marketplace(os.getenv('GIGBID_MODE','local'),os.getenv('GIGBID_DB_PATH','gigbid.sqlite'))
READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True)
WRITE=ToolAnnotations(readOnlyHint=False,destructiveHint=True,idempotentHint=True)
JobId=Annotated[str,Field(min_length=1,max_length=128)]
WriteKey=Annotated[str,Field(min_length=8,max_length=128)]
ProposalText=Annotated[str,Field(min_length=10,max_length=10000)]

@mcp.tool(annotations=READ)
def search_jobs(query:str='')->list[dict]:
    """Read available marketplace jobs matching a search query."""
    return port.search_jobs(query)

@mcp.tool(annotations=READ)
def get_job(job_id:JobId)->dict:
    """Read a full job record."""
    return port.get_job(job_id) or {}

@mcp.tool(annotations=READ)
def get_client_history(client_id:JobId)->dict:
    """Read verified client history and risk signals."""
    return port.get_client_history(client_id)

@mcp.tool(annotations=READ)
def get_connects_balance()->int:
    """Read the remaining application balance."""
    return port.get_connects_balance()

@mcp.tool(annotations=READ)
def list_messages(job_id:JobId)->list[dict]:
    """Read a job's client conversation."""
    return port.list_messages(job_id)

@mcp.tool(annotations=WRITE)
def create_proposal_draft(job_id:JobId,text:ProposalText,idempotency_key:WriteKey,dry_run:bool=True)->dict:
    """Create an unsent proposal draft after GigBid approval; preview by default."""
    return port.create_proposal_draft(job_id,text,idempotency_key,dry_run)

@mcp.tool(annotations=WRITE)
def submit_proposal(job_id:JobId,text:ProposalText,idempotency_key:WriteKey,dry_run:bool=True)->dict:
    """Spend Connects and submit only after human approval; preview by default."""
    return port.submit_proposal(job_id,text,idempotency_key,dry_run)

@mcp.tool(annotations=WRITE)
def send_message(job_id:JobId,body:ProposalText,idempotency_key:WriteKey,dry_run:bool=True)->dict:
    """Send a client message only after human approval; preview by default."""
    return port.send_message(job_id,body,idempotency_key,dry_run)

if __name__=='__main__':mcp.run()
