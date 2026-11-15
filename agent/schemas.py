from pydantic import BaseModel, Field

class JobSpec(BaseModel):
    job_id: str
    title: str
    requirements: list[str]
    deliverables: list[str]
    budget_min: float = Field(ge=0)
    budget_max: float = Field(ge=0)
    screening_questions: list[str] = []

class RiskReport(BaseModel):
    score: float = Field(ge=0, le=1)
    flags: list[str]
    rationale: str

class FitReport(BaseModel):
    score: float = Field(ge=0, le=1)
    matched: dict[str,list[str]]
    missing: list[str]

class BidDecision(BaseModel):
    action: str
    rationale: str

class PriceQuote(BaseModel):
    amount: float = Field(ge=0)
    connects: int = Field(ge=0)
    rationale: str

class ProposalDraft(BaseModel):
    text: str
    claim_evidence: dict[str,list[str]]

class Critique(BaseModel):
    pass_review: bool
    reasons: list[str]

class ComplianceVerdict(BaseModel):
    allowed: bool
    reasons: list[str]
