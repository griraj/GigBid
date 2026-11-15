from data.synthetic import EVIDENCE
from rag.retriever import EvidenceIndex
from rag.verify import verify
from agent.schemas import ProposalDraft

def test_persona_scoping():
    idx=EvidenceIndex(EVIDENCE)
    for variant in ['v0','v1','v2','v3','v4','v8']:
        assert all(e['persona']=='ai' for e in idx.search('python classification',variant=variant,persona='ai'))

def test_claims_without_evidence_rejected():
    draft=ProposalDraft(text='I built a spaceship. I delivered retention modelling [e1].',claim_evidence={})
    clean,rejected=verify(draft,[EVIDENCE[0]])
    assert len(rejected)==1
    assert 'spaceship' not in clean
    assert 'retention' in clean


def test_unrelated_claim_cannot_borrow_valid_citation():
    draft=ProposalDraft(text='I built a lunar rover [e1]. I guarantee perfect accuracy.',claim_evidence={})
    clean,rejected=verify(draft,[EVIDENCE[0]])
    assert clean == ''
    assert len(rejected)==2


def test_uncited_experience_in_profile_introduction_is_removed():
    draft=ProposalDraft(text='I am a Python developer with experience in building churn prediction pipelines. I would confirm your milestones.',claim_evidence={})
    clean,rejected=verify(draft,EVIDENCE)
    assert len(rejected)==1
    assert clean=='I would confirm your milestones.'
