"""Independent read-only MCP portfolio server: python -m mcp_servers.portfolio.server"""
from mcp.server.fastmcp import FastMCP
from data.synthetic import EVIDENCE
from rag.retriever import EvidenceIndex
import json

mcp=FastMCP('GigBid Evidence Vault')
index=EvidenceIndex(EVIDENCE)

@mcp.tool()
def search_evidence(requirement:str,k:int=5,persona:str='ai',filters:dict|None=None)->list[dict]:
    """Search attributable work samples for a requirement; optionally filter by type or outcome."""
    if not 1<=k<=20: raise ValueError('k must be 1-20')
    hits=index.search(requirement,k=20,persona=persona)
    filters=filters or {}
    return [h for h in hits if all(h.get(field)==value for field,value in filters.items())][:k]

@mcp.tool()
def get_case_study(id:str)->dict:
    """Retrieve one full case study by its stable evidence ID."""
    return next((e for e in EVIDENCE if e['id']==id and e['type']=='case_study'),{})

@mcp.tool()
def list_skills(persona:str='ai')->list[str]:
    """List skills demonstrated by this person's evidence."""
    return sorted(set(skill for e in EVIDENCE if e['persona']==persona for skill in e['skills']))

@mcp.resource('portfolio://case/{id}')
def case_resource(id:str)->str:return json.dumps(get_case_study(id))

@mcp.resource('portfolio://proposal/{id}')
def proposal_resource(id:str)->str:return json.dumps(next((e for e in EVIDENCE if e['id']==id and e['type']=='proposal'),{}))

@mcp.prompt()
def answer_screening_question(question:str)->str:
    return f'Answer this question using only evidence from search_evidence, cite item IDs, and say when evidence is missing: {question}'

if __name__=='__main__':mcp.run()
