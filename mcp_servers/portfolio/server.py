"""Independent read-only MCP portfolio server: python -m mcp_servers.portfolio.server"""
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from data.synthetic import EVIDENCE
from rag.retriever import EvidenceIndex
from rag.ingest_portfolio import load_portfolio
from data.portfolio_store import PortfolioStore
from agent.paths import data_path
import json
import os
from pathlib import Path

mcp=FastMCP('GigBid Evidence Vault')
READ=ToolAnnotations(readOnlyHint=True,destructiveHint=False,idempotentHint=True)
tenant_id=os.getenv('GIGBID_TENANT_ID','reviewer')
multi=os.getenv('GIGBID_AUTH_MODE')=='multi'
items=EVIDENCE+([] if multi else load_portfolio())

def tenant_items(persona:str='ai')->list[dict]:
    if not multi or tenant_id=='reviewer':return items
    records=PortfolioStore(data_path('portfolio_uploads.sqlite')).list(tenant_id)
    return items+[{'id':record['id'],'title':record['filename'],'text':record['text'],
        'persona':persona,'type':'portfolio_document','skills':[],
        'outcome':'unverified','source':'user_uploaded','date':record['created']} for record in records]

def current_index(persona='ai'):
    # Per-user uploads may arrive while a persistent MCP session is alive.
    # Rebuild the small tenant index on demand to avoid stale search results.
    return EvidenceIndex(tenant_items(persona)) if multi else index
if os.getenv('GIGBID_RAG_BACKEND','lexical')=='ollama-vector':
    from rag.ollama_vector import build_ollama_index
    index=build_ollama_index(items)
elif os.getenv('GIGBID_RAG_BACKEND','lexical')=='neural':
    from rag.neural import NeuralEvidenceIndex
    index=NeuralEvidenceIndex(items,model_name=os.getenv('GIGBID_EMBEDDING_MODEL','sentence-transformers/all-MiniLM-L6-v2'),
                              directory=str(Path(__file__).resolve().parents[2]/'data/processed/chroma'))
else:index=EvidenceIndex(items)

@mcp.tool(annotations=READ)
def search_evidence(requirement:str,k:int=5,persona:str='ai',filters:dict|None=None)->list[dict]:
    """Search attributable work samples for a requirement; optionally filter by type or outcome."""
    if not 1<=k<=20: raise ValueError('k must be 1-20')
    hits=current_index(persona).search(requirement,k=20,persona=persona)
    filters=filters or {}
    return [h for h in hits if all(h.get(field)==value for field,value in filters.items())][:k]

@mcp.tool(annotations=READ)
def get_case_study(id:str)->dict:
    """Retrieve one full case study by its stable evidence ID."""
    return next((e for e in tenant_items() if e['id']==id and e['type'] in ('case_study','portfolio_document')), {})

@mcp.tool(annotations=READ)
def list_skills(persona:str='ai')->list[str]:
    """List skills demonstrated by this person's evidence."""
    return sorted(set(skill for e in tenant_items(persona) if e['persona']==persona for skill in e['skills']))

@mcp.resource('portfolio://case/{id}')
def case_resource(id:str)->str:return json.dumps(get_case_study(id))

@mcp.resource('portfolio://proposal/{id}')
def proposal_resource(id:str)->str:return json.dumps(next((e for e in EVIDENCE if e['id']==id and e['type']=='proposal'),{}))

@mcp.prompt()
def answer_screening_question(question:str)->str:
    return f'Answer this question using only evidence from search_evidence, cite item IDs, and say when evidence is missing: {question}'

if __name__=='__main__':mcp.run()
