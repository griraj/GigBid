"""Durable parallel bid decision graph with an interrupt-mediated approval gate."""
from __future__ import annotations
from typing import TypedDict
from langgraph.graph import StateGraph,START,END
from langgraph.types import interrupt,Send
from agent.schemas import JobSpec,RiskReport,FitReport,BidDecision,PriceQuote,ProposalDraft,Critique,ComplianceVerdict
from rag.verify import verify
import re
import os
from agent.mcp_client import MCPRouter

INJECTION=re.compile(r'(ignore (?:all|any|previous)|system\s*:|developer\s*:|override (?:safety|instructions))',re.I)
FORBIDDEN=re.compile(r'(telegram|whatsapp|off.platform|outside (?:the )?platform|deposit|passport|credit card|free (?:production|sample)|unpaid (?:trial|sample))',re.I)
CONTACT=re.compile(r'[\w.%-]+@[\w.-]+\.[a-z]{2,}|(?:\+?\d[\d -]{8,}\d)',re.I)

class BidState(TypedDict,total=False):
    job:dict
    persona:str
    spec:dict
    risk:dict
    fit:dict
    evidence:list[dict]
    decision:dict
    price:dict
    draft:dict
    critique:dict
    compliance:dict
    revision:int
    approval:dict
    result:dict
    status:str

def build_bid_graph(marketplace,index,config,checkpointer):
    tool_router=MCPRouter()
    def marketplace_read(role,name,args):
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            return tool_router.call(role,'marketplace',name,args)
        if name=='get_client_history':return marketplace.get_client_history(args['client_id'])
        return getattr(marketplace,name)(**args)
    def evidence_search(requirement,persona):
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            return tool_router.call('fit','portfolio','search_evidence',{'requirement':requirement,'persona':persona,'k':5})
        return index.search(requirement,k=5,variant=config.get('rag_variant','v2'),persona=persona)
    def marketplace_write(name,job_id,text,key,dry_run):
        if os.getenv('GIGBID_TOOL_BACKEND','mcp')=='mcp':
            field='text' if name!='send_message' else 'body'
            return tool_router.call('approval','marketplace',name,{'job_id':job_id,field:text,'idempotency_key':key,'dry_run':dry_run})
        return getattr(marketplace,name)(job_id,text,key,dry_run=dry_run)
    def analyst(s):
        j=s['job']; spec=JobSpec(job_id=j['id'],title=j['title'],requirements=j['skills'],deliverables=[j['title']],budget_min=j['min_budget'],budget_max=j['max_budget'])
        return {'spec':spec.model_dump()}
    def risk(s):
        j=s['job'];c=marketplace_read('risk','get_client_history',{'client_id':j['client_id']}); flags=[]
        if not c.get('payment_verified'):flags.append('unverified_payment')
        if FORBIDDEN.search(j['description']):flags.append('free_work_or_off_platform')
        if INJECTION.search(j['description']): flags.append('prompt_injection')
        score=min(1,0.22*len(flags)+ (0.42 if c.get('hire_rate',0)<0.1 else 0))
        return {'risk':RiskReport(score=score,flags=flags,rationale='Rule-based screening; job text treated as untrusted data.').model_dump()}
    def fit(s):
        j=s['job']; found={}; evidence={}
        for req in j['skills']:
            hits=[e for e in evidence_search(req,s['persona'])
                  if req.lower() in [v.lower() for v in e['skills']] or
                  (e.get('type')=='portfolio_document' and req.lower() in e['text'].lower())]
            found[req]=[e['id'] for e in hits]
            for e in hits:evidence[e['id']]=e
        missing=[r for r,ids in found.items() if not ids]
        score=(len(j['skills'])-len(missing))/max(len(j['skills']),1)
        return {'fit':FitReport(score=score,matched=found,missing=missing).model_dump(),'evidence':list(evidence.values())}
    def decide(s):
        r=s['risk'];f=s['fit']; hard_block=bool(set(r['flags'])&set(config.get('block_risk_flags',['prompt_injection','free_work_or_off_platform'])))
        action='skip' if hard_block or r['score']>=0.55 else 'bid' if f['score']>=config.get('minimum_fit',0.3) else 'watch'
        if s['job'].get('provenance',{}).get('kind')=='real_export' and action=='bid':action='watch'
        reason='High risk' if action=='skip' else 'Portfolio evidence supports requirements' if action=='bid' else 'Insufficient demonstrated fit'
        if s['job'].get('provenance',{}).get('kind')=='real_export':reason='Research-only imported job: analysis is allowed, but submission is disabled in local mode.'
        return {'decision':BidDecision(action=action,rationale=reason).model_dump(),'status':action}
    def decision_route(s):return 'price' if s['decision']['action']=='bid' else END
    def price(s):
        j=s['job'];floor=config.get('hourly_floor',22)*max(1,min(20,len(j['skills'])*3))
        connects_available=marketplace_read('pricing','get_connects_balance',{})
        suggested=max(j['min_budget'],min(j['max_budget'],round((j['min_budget']+j['max_budget'])/2)))
        return {'price':PriceQuote(amount=suggested,connects=j['connects'],rationale=f'Midpoint of stated budget; floor estimate ${floor:.0f}; marketplace balance {connects_available}, no guarantee of profit.').model_dump()}
    def write(s):
        j=s['job'];ev=s.get('evidence',[])
        lines=[f"Hello, I can help with {j['title'].lower()}."]
        mapping={}
        for e in ev[:3]:
            if e.get('type')=='proposal':
                sentence=f"My previous proposal discussed {e['title'].lower()} [{e['id']}]."
            elif e.get('outcome')=='unverified':
                sentence=f"My uploaded portfolio document discusses {e['title'].lower()} [{e['id']}]."
            else:
                sentence=f"I delivered {e['title'].lower()} using {', '.join(e['skills'][:3])} [{e['id']}]."
            lines.append(sentence);mapping[sentence]=[e['id']]
        lines.append('I would confirm deliverables and milestones before starting. Would you be open to discussing the scope?')
        proposed=' '.join(lines)
        model_usage={}
        import os
        if os.getenv('GIGBID_LLM_BACKEND','template')=='ollama':
            from agent.llm import draft_details_with_ollama
            model=config['models'][os.getenv('GIGBID_MODEL_PROFILE','open')]['writer']
            model_result=draft_details_with_ollama(j,ev,model)
            proposed=model_result['text']
            model_usage={key:value for key,value in model_result.items() if key not in ('text','raw_response')}
            mapping={sentence:re.findall(r'\[([a-z][a-z0-9_-]{1,40})\]',sentence)
                for sentence in re.split(r'(?<=[.!?])\s+',proposed.strip())
                if re.search(r'\[[a-z][a-z0-9_-]{1,40}\]',sentence)}
        proposal=ProposalDraft(text=proposed,claim_evidence=mapping)
        verified,rejected=verify(proposal,ev)
        return {'draft':{'text':verified,'claim_evidence':mapping,'removed_claims':rejected,'model_usage':model_usage}}
    def critic(s):
        text=s['draft']['text'];reasons=[]
        if len(text)<90:reasons.append('Draft is too brief')
        if not s.get('evidence'):reasons.append('No portfolio evidence available')
        usage=s['draft'].get('model_usage',{})
        if usage.get('done_reason')=='length':reasons.append('Model output was truncated; increase its budget or choose another model')
        if usage and not re.search(r'\[[a-z][a-z0-9_-]{1,40}\]',text):reasons.append('Model draft has no usable evidence citations')
        return {'critique':Critique(pass_review=not reasons,reasons=reasons).model_dump()}
    def critic_route(s):
        if not s['critique']['pass_review'] and s.get('revision',0)<config.get('max_critic_revisions',2):return 'revise'
        return 'compliance'
    def revise(s):
        draft=dict(s['draft']);draft['text']+=' I can share a concise milestone plan once we agree on priorities.'
        return {'revision':s.get('revision',0)+1,'draft':draft}
    def compliance(s):
        content=s['draft']['text'];reasons=[]
        if not s['critique']['pass_review']:reasons.extend(s['critique']['reasons'])
        if CONTACT.search(content) or FORBIDDEN.search(content):reasons.append('Contact or prohibited arrangement detected')
        _,invalid=verify(ProposalDraft(**{k:s['draft'][k] for k in ('text','claim_evidence')}),s.get('evidence',[]))
        if invalid: reasons.append('Unsupported claims')
        return {'compliance':ComplianceVerdict(allowed=not reasons,reasons=reasons).model_dump(),'status':'awaiting_approval' if not reasons else 'blocked'}
    def guard_route(s):return 'approval' if s['compliance']['allowed'] else END
    def approval(s):
        preview=marketplace_write('submit_proposal',s['job']['id'],s['draft']['text'],'preview-only',True)
        choice=interrupt({'job_id':s['job']['id'],'draft':s['draft'],'evidence':s['evidence'],'risk':s['risk'],'price':s['price'],'preview':preview})
        if not isinstance(choice,dict) or choice.get('action')!='approve':return {'approval':choice or {'action':'reject'},'status':'rejected'}
        text=choice.get('text',s['draft']['text'])
        verified,rejected=verify(ProposalDraft(text=text,claim_evidence=s['draft']['claim_evidence']),s['evidence'])
        if rejected or CONTACT.search(verified) or FORBIDDEN.search(verified):return {'status':'blocked','approval':{'action':'blocked','reason':'Edited draft failed verification'}}
        return {'approval':{'action':'approve','text':verified},'status':'approved'}
    def approval_route(s):return 'submit' if s['status']=='approved' else END
    def submit(s):
        from uuid import uuid5,NAMESPACE_URL
        key=str(uuid5(NAMESPACE_URL,'bid:'+s['job']['id']+':'+s['persona']))
        result=marketplace_write('submit_proposal',s['job']['id'],s['approval']['text'],key,False)
        return {'result':result,'status':'submitted'}
    graph=StateGraph(BidState)
    for name,fn in [('analyst',analyst),('risk',risk),('fit',fit),('decide',decide),('price',price),('writer',write),('critic',critic),('revise',revise),('compliance',compliance),('approval',approval),('submit',submit)]:graph.add_node(name,fn)
    graph.add_conditional_edges(START,lambda s:[Send(name,s) for name in ('analyst','risk','fit')],['analyst','risk','fit'])
    for node in ['analyst','risk','fit']:graph.add_edge(node,'decide')
    graph.add_conditional_edges('decide',decision_route)
    graph.add_edge('price','writer');graph.add_edge('writer','critic')
    graph.add_conditional_edges('critic',critic_route,{'revise':'revise','compliance':'compliance'})
    graph.add_edge('revise','critic');graph.add_conditional_edges('compliance',guard_route,{'approval':'approval',END:END})
    graph.add_conditional_edges('approval',approval_route,{'submit':'submit',END:END});graph.add_edge('submit',END)
    return graph.compile(checkpointer=checkpointer)
