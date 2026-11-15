"""Conservative, evidence-grounded replacement suggestions for the proposal studio.

Suggestions never submit a proposal or change a checkpoint. The human must
review the suggestion and approve the full proposal through the graph gate.
"""
from __future__ import annotations

import re

from agent.schemas import ProposalDraft
from rag.verify import verify


def regenerate_paragraph(draft: str, paragraph_index: int, evidence: list[dict]) -> dict:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", draft) if p.strip()]
    if not paragraphs:
        raise ValueError("No proposal paragraph to regenerate")
    if paragraph_index < 0 or paragraph_index >= len(paragraphs):
        raise ValueError("Paragraph index is out of range")
    if not evidence:
        raise ValueError("No verified portfolio evidence is available")

    # Reuse evidence attributes verbatim; never invent numeric accomplishments.
    supported = [item for item in evidence if item.get("outcome") != "unverified"]
    if not supported:
        raise ValueError("Only unverified portfolio evidence is available")
    item = supported[paragraph_index % len(supported)]
    title = str(item["title"]).strip()
    identifier = str(item["id"])
    # Titles are the safest precise claims: skills metadata might not occur
    # in the source document text and must not be silently treated as proof.
    sentence = f"I delivered {title.lower()} [{identifier}]."
    safe, rejected = verify(ProposalDraft(text=sentence, claim_evidence={sentence: [identifier]}), supported)
    if rejected or not safe:
        raise ValueError("Portfolio evidence did not pass the claim verifier")

    paragraphs[paragraph_index] = safe
    return {"paragraph_index": paragraph_index, "suggestion": safe, "text": "\n\n".join(paragraphs),
            "evidence_ids": [identifier], "requires_approval": True,
            "method": "deterministic_evidence_template"}
