import os
from mcp.server.fastmcp import FastMCP
from agent.marketplace_port import build_marketplace

mcp=FastMCP('GigBid Marketplace Gateway')
port=build_marketplace(os.getenv('GIGBID_MODE','local'),os.getenv('GIGBID_DB_PATH','gigbid.sqlite'))

@mcp.tool()
def search_jobs(query:str='')->list[dict]:
    """Read available marketplace jobs matching a search query."""
    return port.search_jobs(query)

@mcp.tool()
def get_job(job_id:str)->dict:
    """Read a full job record."""
    return port.get_job(job_id) or {}

@mcp.tool()
def get_client_history(client_id:str)->dict:
    """Read verified client history and risk signals."""
    return port.get_client_history(client_id)

@mcp.tool()
def get_connects_balance()->int:
    """Read the remaining application balance."""
    return port.get_connects_balance()

@mcp.tool()
def list_messages(job_id:str)->list[dict]:
    """Read a job's client conversation."""
    return port.list_messages(job_id)

@mcp.tool()
def create_proposal_draft(job_id:str,text:str,idempotency_key:str,dry_run:bool=True)->dict:
    """Create an unsent proposal draft after GigBid approval; preview by default."""
    return port.create_proposal_draft(job_id,text,idempotency_key,dry_run)

@mcp.tool()
def submit_proposal(job_id:str,text:str,idempotency_key:str,dry_run:bool=True)->dict:
    """Spend Connects and submit only after human approval; preview by default."""
    return port.submit_proposal(job_id,text,idempotency_key,dry_run)

@mcp.tool()
def send_message(job_id:str,body:str,idempotency_key:str,dry_run:bool=True)->dict:
    """Send a client message only after human approval; preview by default."""
    return port.send_message(job_id,body,idempotency_key,dry_run)

if __name__=='__main__':mcp.run()
