import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    learning_objectives = Column(JSON, nullable=False, default=list)  # List of strings
    target_audience = Column(String(100), nullable=False, default="Undergraduate / Intermediate")
    difficulty_level = Column(String(50), nullable=False, default="Intermediate")
    estimated_duration_mins = Column(Integer, nullable=False, default=45)
    
    # Structured JSON content blocks: introduction, prerequisites, core_modules, assessments, summary
    content_blocks = Column(JSON, nullable=False, default=dict)
    
    # Status: DRAFT, GENERATED, EDITED_PENDING_QC, FULLY_REVIEWED
    status = Column(String(50), nullable=False, default="DRAFT", index=True)
    current_version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    sources = relationship("ResearchSource", back_populates="lesson", cascade="all, delete-orphan")
    factual_qc_reports = relationship("FactualQCReport", back_populates="lesson", cascade="all, delete-orphan")
    instructional_qc_reports = relationship("InstructionalQCReport", back_populates="lesson", cascade="all, delete-orphan")
    revisions = relationship("LessonRevision", back_populates="lesson", cascade="all, delete-orphan")
    tasks = relationship("GenerationTask", back_populates="lesson", cascade="all, delete-orphan")
