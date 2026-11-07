from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ClaimVerificationItem(BaseModel):
    claim: str
    verdict: str  # 'VERIFIED', 'CONTRADICTED', 'UNSUBSTANTIATED', 'PARTIALLY_SUPPORTED'
    evidence_quote: Optional[str] = None
    source_reference_tag: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    recommended_correction: Optional[str] = None


class FactualQCReportResponse(BaseModel):
    id: str
    lesson_id: str
    lesson_version: int
    status: str = "PASSED"
    factual_accuracy_score: float
    claim_verification_rate: float
    citation_fidelity_score: float
    hallucination_penalty: float
    total_claims_analyzed: int
    verified_claims_count: int
    partially_supported_count: int
    unsubstantiated_count: int
    contradicted_count: int
    claim_verifications: List[ClaimVerificationItem]
    hallucination_flags: List[Dict[str, Any]]
    missing_citations: List[Dict[str, Any]]
    executive_summary: str
    recommended_corrections: List[str]
    is_stale: bool
    stale_reason: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class RubricCriterion(BaseModel):
    name: str
    weight: float
    score: float
    description: str
    evidence: str


class InstructionalQCReportResponse(BaseModel):
    id: str
    lesson_id: str
    lesson_version: int
    status: str = "PASSED"
    pedagogical_score: float
    bloom_alignment_score: float
    clarity_score: float
    scaffolding_score: float
    assessment_fidelity_score: float
    engagement_score: float
    target_bloom_level: str
    achieved_bloom_level: str
    bloom_verb_analysis: Dict[str, Any]
    rubric_breakdown: List[RubricCriterion]
    strengths: List[str]
    actionable_improvements: List[str]
    executive_summary: str
    is_stale: bool
    stale_reason: Optional[str] = None
    generated_at: datetime

    class Config:
        from_attributes = True


class DualQCResponse(BaseModel):
    status: str
    message: str
    factual_qc: Optional[FactualQCReportResponse] = None
    instructional_qc: Optional[InstructionalQCReportResponse] = None


class QCSummaryResponse(BaseModel):
    lesson_id: str
    lesson_version: int
    is_stale: bool
    stale_reason: Optional[str] = None
    factual_qc: Optional[FactualQCReportResponse] = None
    instructional_qc: Optional[InstructionalQCReportResponse] = None

