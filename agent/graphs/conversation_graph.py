from typing import TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.types import interrupt
from agent.graphs.bid_graph import FORBIDDEN,CONTACT,INJECTION
from uuid import uuid5,NAMESPACE_URL
import os
from agent.mcp_client import MCPRouter

class ConversationState(TypedDict,total=False):
    job_id:str
    incoming:str
    intent:str
    suggestion:str
    status:str
    approval:dict
    result:dict

def build_conversation_graph(marketplace,checkpointer):
    router=MCPRouter()
    def liaison(s):
        content=s['incoming'];intent='scam' if FORBIDDEN.search(content) or INJECTION.search(content) else 'interview' if 'interview' in content.lower() else 'negotiation' if 'budget' in content.lower() or 'rate' in content.lower() else 'question'
        reply='Thank you for reaching out. I would be happy to discuss milestones and requirements here on the platform.' if intent!='scam' else ''
        return {'intent':intent,'suggestion':reply,'status':'blocked' if intent=='scam' else 'awaiting_approval'}
    def route(s):return END if s['status']=='blocked' else 'approval'
    def approval(s):
        choice=interrupt({'intent':s['intent'],'draft':s['suggestion'],'job_id':s['job_id']})
        if choice.get('action')!='approve':return {'status':'rejected','approval':choice}
        body=choice.get('text',s['suggestion'])
        if FORBIDDEN.search(body) or CONTACT.search(body):return {'status':'blocked'}
        return {'approval':{'text':body},'status':'approved'}
    def next_step(s):return 'send' if s['status']=='approved' else END
    def send(s):
        key=str(uuid5(NAMESPACE_URL,'reply:'+s['job_id']+':'+s['incoming']))
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            result=router.call('approval','marketplace','send_message',{'job_id':s['job_id'],'body':s['approval']['text'],'idempotency_key':key,'dry_run':False})
        else:result=marketplace.send_message(s['job_id'],s['approval']['text'],key)
        return {'result':result,'status':'sent'}
    g=StateGraph(ConversationState)
    for n,f in [('liaison',liaison),('approval',approval),('send',send)]:g.add_node(n,f)
    g.add_edge(START,'liaison');g.add_conditional_edges('liaison',route);g.add_conditional_edges('approval',next_step);g.add_edge('send',END)
    return g.compile(checkpointer=checkpointer)
