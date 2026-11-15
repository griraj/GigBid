from datetime import datetime,timedelta,timezone
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from uuid import uuid4

mcp=FastMCP('GigBid Workspace')
READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True)
WRITE=ToolAnnotations(readOnlyHint=False,destructiveHint=False,idempotentHint=False)
holds={};drafts={}

@mcp.tool(annotations=READ)
def free_calendar_slots(days:int=7)->list[str]:
    """Get simulated available UTC interview slots for the next 1-14 days."""
    if not 1<=days<=14:raise ValueError('days 1-14')
    start=datetime.now(timezone.utc).replace(hour=12,minute=0,second=0,microsecond=0)
    return [(start+timedelta(days=d)).isoformat() for d in range(1,days+1) if (start+timedelta(days=d)).weekday()<5]

@mcp.tool(annotations=WRITE)
def create_interview_hold(slot:str,job_id:str)->dict:
    """Create a tentative local interview hold; does not invite or notify anyone."""
    datetime.fromisoformat(slot.replace('Z','+00:00'))
    id=str(uuid4());holds[id]={'slot':slot,'job_id':job_id};return {'id':id,**holds[id]}

@mcp.tool(annotations=WRITE)
def create_email_draft(subject:str,body:str)->dict:
    """Save an unsent local email draft; never send email."""
    id=str(uuid4());drafts[id]={'subject':subject,'body':body};return {'id':id,'status':'draft'}

if __name__=='__main__':mcp.run()
