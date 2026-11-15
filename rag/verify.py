"""Conservative citation and numeric-claim gate, not semantic entailment proof."""
import re

def verify(draft, evidence):
    items={e['id']:e for e in evidence}
    good=[]; rejected=[]
    for sentence in re.split(r'(?<=[.!?])\s+',draft.text.strip()):
        if not sentence: continue
        citations=set(re.findall(r'\[([a-z][a-z0-9_-]{1,40})\]',sentence))
        # Explicit experience assertions without concrete evidence are dropped.
        experience=bool(re.search(r'\b(?:I|we|our team|my team)\s+(?:built|implemented|delivered|trained|created|have|developed|led|managed|worked|achieved|increased|reduced|improved|specialize)|\bmy\s+(?:work|experience|clients|projects)\b',sentence,re.I))
        numerics=re.findall(r'\b\d+(?:\.\d+)?%?\b',re.sub(r'\[[a-z][a-z0-9_-]{1,40}\]','',sentence))
        supported_numbers=' '.join(items[id]['text'] for id in citations if id in items)
        unsupported_number=bool(experience and any(number not in supported_numbers for number in numerics))
        if experience and (not citations or not citations.issubset(items) or unsupported_number):
            rejected.append(sentence)
        else:
            good.append(sentence)
    return ' '.join(good),rejected
