from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class LessonGenerateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Lesson title")
    learning_objectives: List[str] = Field(..., min_items=1, description="List of learning objectives")
    target_audience: str = Field(default="Undergraduate / Intermediate")
    difficulty_level: str = Field(default="Intermediate")
    estimated_duration_mins: int = Field(default=45, ge=10, le=45)


class LessonCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=255, description="Lesson title")
    learning_objectives: List[str] = Field(..., min_items=1, description="List of learning objectives")
    target_audience: str = Field(default="Undergraduate / Intermediate")
    difficulty_level: str = Field(default="Intermediate")
    estimated_duration_mins: int = Field(default=45, ge=10, le=45)


class LessonUpdateRequest(BaseModel):
    title: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    target_audience: Optional[str] = None
    difficulty_level: Optional[str] = None
    estimated_duration_mins: Optional[int] = Field(default=None, le=45)
    content_blocks: Optional[Dict[str, Any]] = None
    editor_notes: Optional[str] = Field(default="Instructor updated content")


# =====================================================================
# Phase 3: Structured Pedagogical Lesson Schemas (Enforced with Pydantic)
# =====================================================================

class PrerequisiteItem(BaseModel):
    concept: str
    brief_refresher: str


class CoreConceptSection(BaseModel):
    title: str
    explanation: str
    key_takeaway: str
    supporting_citation_tags: List[str] = Field(default_factory=list)
    estimated_minutes: int = Field(default=5, ge=1, le=25)


class PracticalExample(BaseModel):
    title: str
    scenario: str
    code_or_walkthrough: str
    explanation: str
    estimated_minutes: int = Field(default=5, ge=1, le=15)


class RealWorldApplication(BaseModel):
    domain: str
    use_case: str
    trade_offs: str


class GuidedExercise(BaseModel):
    title: str
    problem_statement: str
    hints: List[str] = Field(default_factory=list)
    solution: str
    estimated_minutes: int = Field(default=5, ge=1, le=15)


class KnowledgeCheck(BaseModel):
    question: str
    question_type: str = Field(default="multiple_choice")  # multiple_choice, conceptual_analysis
    options: Optional[List[str]] = None
    correct_answer: str
    rationale: str
    target_objective: str


class ReferenceItem(BaseModel):
    citation_tag: str
    title: str
    url_or_identifier: Optional[str] = None
    is_content_accessible: bool
    verification_scope_note: Optional[str] = None


class StructuredLessonContent(BaseModel):
    overview: str
    learning_objectives: List[str]
    target_audience: str
    difficulty_level: str
    total_estimated_duration_mins: int = Field(default=45, le=45)
    introduction_and_motivation: str
    prerequisite_knowledge: List[PrerequisiteItem]
    core_concepts: List[CoreConceptSection]
    practical_examples: List[PracticalExample]
    real_world_applications: List[RealWorldApplication]
    guided_exercises: List[GuidedExercise]
    knowledge_checks: List[KnowledgeCheck]
    lesson_summary: str
    further_learning_resources: List[str]
    references: List[ReferenceItem]

    @field_validator("total_estimated_duration_mins")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if v > 45:
            raise ValueError(f"Total lesson duration must not exceed 45 minutes (got {v})")
        return v


class LessonSummary(BaseModel):
    id: str
    title: str
    target_audience: str
    difficulty_level: str
    estimated_duration_mins: int
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime
    factual_score: Optional[float] = None
    pedagogical_score: Optional[float] = None
    is_qc_stale: bool = False

    class Config:
        from_attributes = True


class LessonDetail(BaseModel):
    id: str
    title: str
    learning_objectives: List[str]
    target_audience: str
    difficulty_level: str
    estimated_duration_mins: int
    content_blocks: Dict[str, Any]
    status: str
    current_version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonRevisionResponse(BaseModel):
    id: str
    lesson_id: str
    revision_number: int
    content_blocks: Dict[str, Any]
    editor_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
