import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class InstructionalQCReport(Base):
    __tablename__ = "instructional_qc_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_version = Column(Integer, nullable=False, default=1)
    status = Column(String(30), nullable=False, default="PASSED")  # 'PASSED', 'NEEDS_IMPROVEMENT', 'FAILED'

    # Explicit Criterion Scores (0 to 100)
    pedagogical_score = Column(Float, nullable=False)           # Weighted composite of pedagogical criteria
    bloom_alignment_score = Column(Float, nullable=False)       # Constructive alignment with target Bloom verbs
    clarity_score = Column(Float, nullable=False)               # Cognitive clarity & accessibility
    scaffolding_score = Column(Float, nullable=False)           # Progression from fundamentals to complex concepts
    assessment_fidelity_score = Column(Float, nullable=False)   # Do quizzes evaluate target learning outcomes?
    engagement_score = Column(Float, nullable=False)            # Real-world analogies, code, and active checkpoints

    # Taxonomy Details
    target_bloom_level = Column(String(50), nullable=False)     # e.g., "Analyze / Evaluate"
    achieved_bloom_level = Column(String(50), nullable=False)   # e.g., "Apply"
    bloom_verb_analysis = Column(JSON, nullable=False, default=dict)

    # Detailed Rubric Breakdown (Criterion, Weight, Score, Concrete Evidence)
    rubric_breakdown = Column(JSON, nullable=False, default=list)

    # Pedagogical insights
    strengths = Column(JSON, nullable=False, default=list)
    actionable_improvements = Column(JSON, nullable=False, default=list)
    executive_summary = Column(Text, nullable=False)

    # Revision & Stale Management
    is_stale = Column(Boolean, nullable=False, default=False)
    stale_reason = Column(String(255), nullable=True)

    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    lesson = relationship("Lesson", back_populates="instructional_qc_reports")
