from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ResearchSourceResponse(BaseModel):
    id: str
    lesson_id: str
    source_type: str  # 'web', 'book', 'youtube'
    citation_tag: str  # e.g., '[REF-1]'
    title: str
    url_or_identifier: Optional[str] = None
    author_or_channel: Optional[str] = None
    is_content_accessible: bool
    preview_type: str  # 'full_text', 'snippet', 'metadata_only', 'transcript'
    accessible_text_length: float
    extracted_content: Optional[str] = None
    key_takeaways: Optional[str] = None
    relevance_score: float
    verification_scope_note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResearchSourceCreate(BaseModel):
    source_type: str
    title: str
    url_or_identifier: Optional[str] = None
    author_or_channel: Optional[str] = None
    is_content_accessible: bool = True
    preview_type: str = "snippet"
    extracted_content: Optional[str] = None
    key_takeaways: Optional[str] = None
    verification_scope_note: Optional[str] = None
