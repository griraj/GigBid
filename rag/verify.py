"""Conservative structured claim verification, avoiding an unchecked LLM judge."""
import re

def verify(draft, evidence):
    ids={e['id'] for e in evidence}
    good=[]; rejected=[]
    for sentence in re.split(r'(?<=[.!?])\s+',draft.text.strip()):
        if not sentence: continue
        citations=set(re.findall(r'\[([a-z]\d+)\]',sentence))
        # Explicit experience assertions without concrete evidence are dropped.
        experience=bool(re.search(r'\b(I (?:built|implemented|delivered|trained|created|have)|my (?:work|experience))\b',sentence,re.I))
        if experience and (not citations or not citations.issubset(ids)):
            rejected.append(sentence)
        else:
            good.append(sentence)
    return ' '.join(good),rejected
