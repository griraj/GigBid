"""X5 draft-only negotiation subgraph; parent graph owns the approval boundary."""
import re
from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class NegotiationState(TypedDict,total=False):
    incoming:str
    floor:float
    offered:float|None
    recommendation:float|None
    walk_away:bool
    suggestion:str


def build_negotiation_graph():
    def assess(state):
        match=re.search(r'\$\s*(\d+(?:\.\d+)?)\s*(?:/\s*h(?:r|our)?|per hour|an hour|hourly)|(?:hourly rate|rate per hour)\s*(?:is|of)?\s*\$?\s*(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*(?:/\s*h(?:r|our)?|per hour|an hour)',state['incoming'],re.I)
        amount=float(next(group for group in match.groups() if group)) if match else None
        return {'offered':amount,'walk_away':amount is not None and amount<state['floor']}
    def respond(state):
        amount=state['offered'];floor=state['floor']
        if amount is None:
            return {'recommendation':None,'suggestion':'Could you confirm the hourly rate and scope here on the platform before we agree on terms?'}
        if state['walk_away']:
            return {'recommendation':floor,'suggestion':f'My minimum hourly rate is ${floor:g}. I can discuss a smaller scope at that rate; otherwise I would need to decline this arrangement.'}
        return {'recommendation':amount,'suggestion':f'The proposed ${amount:g} hourly rate is within my range. I would confirm scope, milestones and platform contract terms before agreeing.'}
    graph=StateGraph(NegotiationState)
    graph.add_node('assess_offer',assess);graph.add_node('draft_counteroffer',respond)
    graph.add_edge(START,'assess_offer');graph.add_edge('assess_offer','draft_counteroffer');graph.add_edge('draft_counteroffer',END)
    return graph.compile()
