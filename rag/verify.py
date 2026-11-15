"""Conservative citation and numeric-claim gate, not semantic entailment proof."""
import re

NON_CONTENT=set('i we our my team a an the and or to of for with using have has had built implemented delivered trained created developed led managed worked achieved increased reduced improved specialize in on at by project projects work experience successfully'.split())
GUARANTEE=re.compile(r'\bguarantee(?:d|s)?\b|\b100\s*%\s*(?:accuracy|success)',re.I)


def content_tokens(text):
    return {token for token in re.findall(r'[a-z][a-z0-9-]+',text.lower()) if token not in NON_CONTENT}

def verify(draft, evidence):
    items={e['id']:e for e in evidence}
    good=[]; rejected=[]
    for sentence in re.split(r'(?<=[.!?])\s+',draft.text.strip()):
        if not sentence: continue
        citations=set(re.findall(r'\[([a-z][a-z0-9_-]{1,40})\]',sentence))
        # Explicit experience assertions without concrete evidence are dropped.
        experience=bool(re.search(r'\b(?:I|we|our team|my team)\s+(?:built|implemented|delivered|trained|created|have|developed|led|managed|worked|achieved|increased|reduced|improved|specialize)|\bmy\s+(?:work|experience|clients|projects)\b|\b(?:experience|experienced|expertise|proven track record)\b|^\s*(?:[-*]\s*)?(?:built|implemented|delivered|trained|created|developed|achieved)\b',sentence,re.I))
        numerics=re.findall(r'\b\d+(?:\.\d+)?%?\b',re.sub(r'\[[a-z][a-z0-9_-]{1,40}\]','',sentence))
        supported_numbers=' '.join(items[id]['text'] for id in citations if id in items)
        unsupported_number=bool(experience and any(number not in supported_numbers for number in numerics))
        claim_tokens=content_tokens(re.sub(r'\[[^]]+\]','',sentence))
        support_tokens=content_tokens(' '.join(items[id]['text']+' '+items[id]['title'] for id in citations if id in items))
        # A valid ID alone is insufficient: conservatively abstain when the
        # asserted content is absent. This lexical gate is not NLI entailment.
        content_missing=bool(claim_tokens and len(claim_tokens-support_tokens)/len(claim_tokens)>0.2)
        unverified=any(items[id].get('outcome')=='unverified' for id in citations if id in items)
        if GUARANTEE.search(sentence) or experience and (not citations or not citations.issubset(items) or unsupported_number or content_missing or unverified):
            rejected.append(sentence)
        else:
            good.append(sentence)
    return ' '.join(good),rejected
