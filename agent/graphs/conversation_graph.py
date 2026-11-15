from typing import TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.types import interrupt
from agent.graphs.bid_graph import FORBIDDEN,CONTACT,INJECTION
from uuid import uuid5,NAMESPACE_URL
import os
from agent.mcp_client import MCPRouter
from agent.marketplace_port import local_tenant_marketplace

class ConversationState(TypedDict,total=False):
    owner_id:str
    job_id:str
    incoming:str
    intent:str
    suggestion:str
    status:str
    approval:dict
    result:dict
    negotiation:dict
    slots:list[str]

def build_conversation_graph(marketplace,checkpointer):
    router=MCPRouter()
    def liaison(s):
        content=s['incoming'];intent='scam' if FORBIDDEN.search(content) or INJECTION.search(content) else 'interview' if 'interview' in content.lower() else 'negotiation' if 'budget' in content.lower() or 'rate' in content.lower() else 'question'
        reply='Thank you for reaching out. I would be happy to discuss milestones and requirements here on the platform.' if intent!='scam' else ''
        negotiation={}
        slots=[]
        if intent=='interview':
            from datetime import datetime
            slots=router.call('liaison','workspace','free_calendar_slots',{'days':7},owner_id=s.get('owner_id','reviewer'))
            readable=[datetime.fromisoformat(slot).strftime('%a %d %b, %H:%M UTC') for slot in slots[:3]]
            reply='Available simulated interview slots (UTC): '+', '.join(readable)+'. Which would suit you? I would confirm the appointment here on the platform.'
        if intent=='negotiation':
            import yaml
            from agent.paths import ROOT
            from agent.graphs.negotiation_graph import build_negotiation_graph
            config=yaml.safe_load((ROOT/'agent/config.yaml').read_text())
            negotiation=build_negotiation_graph().invoke({'incoming':content,'floor':float(config['hourly_floor'])})
            reply=negotiation['suggestion']
        return {'intent':intent,'suggestion':reply,'slots':slots,'negotiation':negotiation,'status':'blocked' if intent=='scam' else 'awaiting_approval'}
    def route(s):return END if s['status']=='blocked' else 'approval'
    def approval(s):
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            preview=router.call('liaison','marketplace','send_message',{'job_id':s['job_id'],'body':s['suggestion'],'idempotency_key':'message-preview','dry_run':True},owner_id=s.get('owner_id','reviewer'))
        else:
            port=local_tenant_marketplace(s.get('owner_id','reviewer')) if os.getenv('GIGBID_AUTH_MODE')=='multi' else marketplace
            preview=port.send_message(s['job_id'],s['suggestion'],'message-preview',dry_run=True)
        choice=interrupt({'intent':s['intent'],'draft':s['suggestion'],'job_id':s['job_id'],'slots':s.get('slots',[]),'preview':preview})
        if choice.get('action')!='approve':return {'status':'rejected','approval':choice}
        body=choice.get('text',s['suggestion'])
        if FORBIDDEN.search(body) or CONTACT.search(body):return {'status':'blocked'}
        return {'approval':{'text':body},'status':'approved'}
    def next_step(s):return 'send' if s['status']=='approved' else END
    def send(s):
        key=str(uuid5(NAMESPACE_URL,'reply:'+s['job_id']+':'+s['incoming']))
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            result=router.call('approval','marketplace','send_message',{'job_id':s['job_id'],'body':s['approval']['text'],'idempotency_key':key,'dry_run':False},owner_id=s.get('owner_id','reviewer'))
        else:
            port=local_tenant_marketplace(s.get('owner_id','reviewer')) if os.getenv('GIGBID_AUTH_MODE')=='multi' else marketplace
            result=port.send_message(s['job_id'],s['approval']['text'],key)
        return {'result':result,'status':'sent'}
    g=StateGraph(ConversationState)
    for n,f in [('liaison',liaison),('approval',approval),('send',send)]:g.add_node(n,f)
    g.add_edge(START,'liaison');g.add_conditional_edges('liaison',route);g.add_conditional_edges('approval',next_step);g.add_edge('send',END)
    return g.compile(checkpointer=checkpointer)
