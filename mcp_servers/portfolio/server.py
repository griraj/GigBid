"""Independent read-only MCP portfolio server: python -m mcp_servers.portfolio.server"""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from data.synthetic import EVIDENCE
from rag.retriever import EvidenceIndex
from rag.ingest_portfolio import load_portfolio
import json
import os
from pathlib import Path

mcp=FastMCP('GigBid Evidence Vault')
READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True)
items=EVIDENCE+load_portfolio()
if os.getenv('GIGBID_RAG_BACKEND','lexical')=='neural':
    from rag.neural import NeuralEvidenceIndex
    index=NeuralEvidenceIndex(items,model_name=os.getenv('GIGBID_EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'),
                              directory=str(Path(__file__).resolve().parents[2]/'data/processed/chroma'))
else:index=EvidenceIndex(items)

@mcp.tool(annotations=READ)
def search_evidence(requirement:str,k:int=5,persona:str='ai',filters:dict|None=None)->list[dict]:
    """Search attributable work samples for a requirement; optionally filter by type or outcome."""
    if not 1<=k<=20: raise ValueError('k must be 1-20')
    hits=index.search(requirement,k=20,persona=persona)
    filters=filters or {}
    return [h for h in hits if all(h.get(field)==value for field,value in filters.items())][:k]

@mcp.tool(annotations=READ)
def get_case_study(id:str)->dict:
    """Retrieve one full case study by its stable evidence ID."""
    return next((e for e in items if e['id']==id and e['type'] in ('case_study','portfolio_document')), {})

@mcp.tool(annotations=READ)
def list_skills(persona:str='ai')->list[str]:
    """List skills demonstrated by this person's evidence."""
    return sorted(set(skill for e in items if e['persona']==persona for skill in e['skills']))

@mcp.resource('portfolio://case/{id}')
def case_resource(id:str)->str:return json.dumps(get_case_study(id))

@mcp.resource('portfolio://proposal/{id}')
def proposal_resource(id:str)->str:return json.dumps(next((e for e in EVIDENCE if e['id']==id and e['type']=='proposal'),{}))

@mcp.prompt()
def answer_screening_question(question:str)->str:
    return f'Answer this question using only evidence from search_evidence, cite item IDs, and say when evidence is missing: {question}'

if __name__=='__main__':mcp.run()
