from data.synthetic import EVIDENCE
from rag.retriever import EvidenceIndex

def test_corrective_refuses_unsupported_requirements():
    index=EvidenceIndex(EVIDENCE)
    assert index.search('space elevator maintenance',variant='v8',requirements=['space elevator maintenance'],persona='ai')==[]

def test_corrective_returns_grounded_relevant_evidence():
    index=EvidenceIndex(EVIDENCE)
    hits=index.search('Need Python classification',variant='v8',requirements=['python','classification'],persona='ai')
    assert any(e['id']=='e1' for e in hits)
