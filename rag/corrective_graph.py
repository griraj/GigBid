"""Bounded corrective retrieval StateGraph for weak or missing evidence.

This implements the RAG V8 branch with explicit quality inspection, a
single re-query, and conservative refusal when no requirement is supported.
"""
from __future__ import annotations
from typing import TypedDict
from langgraph.graph import START,END,StateGraph

class RetrievalState(TypedDict,total=False):
    query:str
    requirements:list[str]
    persona:str|None
    k:int
    hits:list[dict]
    attempts:int
    coverage:float

def run_corrective(index,query:str,requirements:list[str]|None=None,persona:str|None=None,k:int=5):
    requirements=requirements or [query]
    def retrieve(s):
        text=s['query'] if s.get('attempts',0)==0 else ' '.join(requirements)
        hits=index.search(text,k=max(k*2,8),variant='v2',persona=persona,requirements=requirements)
        return {'hits':hits,'attempts':s.get('attempts',0)+1}
    def grade(s):
        matched=0
        for requirement in requirements:
            terms=requirement.lower()
            if any(terms in ' '.join(e.get('skills',[])).lower() or terms in e['text'].lower() for e in s['hits']):
                matched+=1
        return {'coverage':matched/max(1,len(requirements))}
    def decide(s):return 'retry' if s['coverage']<0.5 and s['attempts']<2 else 'finish'
    def finish(s):
        return {'hits':s['hits'][:k] if s['coverage']>=0.5 else []}
    graph=StateGraph(RetrievalState)
    graph.add_node('retrieve',retrieve);graph.add_node('grade',grade);graph.add_node('finish',finish)
    graph.add_edge(START,'retrieve');graph.add_edge('retrieve','grade')
    graph.add_conditional_edges('grade',decide,{'retry':'retrieve','finish':'finish'})
    graph.add_edge('finish',END)
    return graph.compile().invoke({'query':query,'requirements':requirements,'persona':persona,'k':k,'attempts':0})['hits']
