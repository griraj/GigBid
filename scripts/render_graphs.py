"""Render graph nodes/edges from the executable LangGraph definitions."""
from pathlib import Path
from xml.sax.saxutils import escape
import yaml
from langgraph.checkpoint.memory import MemorySaver
from agent.graphs.bid_graph import build_bid_graph
from agent.graphs.conversation_graph import build_conversation_graph
from agent.marketplace_port import LocalMarketplace
from rag.retriever import EvidenceIndex
from data.synthetic import EVIDENCE

ROOT=Path(__file__).resolve().parents[1]


def render(graph,name,positions,height):
    diagram=graph.get_graph()
    directory=ROOT/'docs/images';directory.mkdir(parents=True,exist_ok=True)
    (directory/f'{name}.mmd').write_text(diagram.draw_mermaid(),encoding='utf-8')
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{height}" viewBox="0 0 640 {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#8090a0"/></marker></defs>']
    for edge in diagram.edges:
        x1,y1=positions[edge.source];x2,y2=positions[edge.target]
        if edge.target=='__end__' and edge.source not in ('submit','send'):
            route=f'M {x1-70} {y1} C 12 {y1} 12 {y2} {x2-70} {y2}'
        else:route=f'M {x1} {y1+18} L {x2} {y2-20}'
        svg.append(f'<path d="{route}" fill="none" stroke="#8090a0" stroke-width="1.4" marker-end="url(#arrow)"'+(' stroke-dasharray="4 3"' if edge.conditional else '')+'/>')
    for identifier in diagram.nodes:
        x,y=positions[identifier]
        label=identifier.strip('_').replace('_',' ')
        svg.append(f'<rect x="{x-72}" y="{y-18}" width="144" height="36" rx="6" fill="#eef3f7" stroke="#8090a0"/>')
        svg.append(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#223149">{escape(label)}</text>')
    svg.append('</svg>');(directory/f'{name}.svg').write_text('\n'.join(svg),encoding='utf-8')


def main():
    port=LocalMarketplace(':memory:')
    try:
        graph=build_bid_graph(port,EvidenceIndex(EVIDENCE),yaml.safe_load((ROOT/'agent/config.yaml').read_text()),MemorySaver())
        positions={'__start__':(320,35),'analyst':(110,120),'risk':(320,120),'fit':(530,120),
            'decide':(320,210),'price':(320,300),'writer':(320,390),'critic':(320,480),
            'revise':(530,480),'compliance':(320,570),'approval':(320,660),'submit':(320,750),'__end__':(320,840)}
        render(graph,'bid_graph',positions,880)
        render(build_conversation_graph(port,MemorySaver()),'conversation_graph',
            {name:(320,40+i*90) for i,name in enumerate(['__start__','liaison','approval','send','__end__'])},450)
    finally:port.db.close()
    print('Rendered both executable graphs to docs/images/*.svg and *.mmd')


if __name__=='__main__':main()
