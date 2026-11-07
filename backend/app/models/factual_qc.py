import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class FactualQCReport(Base):
    __tablename__ = "factual_qc_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_version = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="PASSED")  # 'PASSED', 'NEEDS_IMPROVEMENT', 'FAILED'

    # Explicit Math-Based Criterion Scores (0 to 100)
    factual_accuracy_score = Column(Float, nullable=False)  # Composite score from weighted criteria
    claim_verification_rate = Column(Float, nullable=False) # % of claims verified against excerpts
    citation_fidelity_score = Column(Float, nullable=False) # % of cited tags that accurately match context
    hallucination_penalty = Column(Float, nullable=False, default=0.0) # Deductions for ungrounded/invented facts

    # Counts
    total_claims_analyzed = Column(Integer, nullable=False, default=0)
    verified_claims_count = Column(Integer, nullable=False, default=0)
    partially_supported_count = Column(Integer, nullable=False, default=0)
    unsubstantiated_count = Column(Integer, nullable=False, default=0)
    contradicted_count = Column(Integer, nullable=False, default=0)

    # Claim-level verification findings:
    # List of {
    #   "claim": str,
    #   "verdict": "VERIFIED" | "CONTRADICTED" | "UNSUBSTANTIATED" | "PARTIALLY_SUPPORTED",
    #   "evidence_quote": str,
    #   "source_reference_tag": str,
    #   "confidence_score": float,
    #   "recommended_correction": Optional[str]
    # }
    claim_verifications = Column(JSON, nullable=False, default=list)

    # Specific issues
    hallucination_flags = Column(JSON, nullable=False, default=list)
    missing_citations = Column(JSON, nullable=False, default=list)

    # Overall summary narrative and actionable feedback
    executive_summary = Column(Text, nullable=False)
    recommended_corrections = Column(JSON, nullable=False, default=list)

    # Revision & Stale Management
    is_stale = Column(Boolean, nullable=False, default=False)
    stale_reason = Column(String(255), nullable=True)

    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    lesson = relationship("Lesson", back_populates="factual_qc_reports")
