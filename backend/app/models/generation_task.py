import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True)

    # Task classifications: 'full_lesson_pipeline', 'qc_rerun', 'research_sync'
    task_type = Column(String(50), nullable=False, default="full_lesson_pipeline")

    # Status: PENDING, RESEARCHING, SYNTHESIZING, QC_EVALUATION, COMPLETED, FAILED
    status = Column(String(50), nullable=False, default="PENDING", index=True)
    current_step = Column(String(100), nullable=False, default="Task initialized")
    progress_percent = Column(Integer, nullable=False, default=0)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Historical timeline logs: [{"timestamp": "...", "stage": "...", "message": "..."}]
    step_logs = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    lesson = relationship("Lesson", back_populates="tasks")
