import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResearchSource(Base):
    __tablename__ = "research_sources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)

    # Source classification: 'web', 'book', 'youtube'
    source_type = Column(String(20), nullable=False)
    citation_tag = Column(String(20), nullable=False)  # e.g., '[REF-1]', '[BOOK-1]', '[YT-1]'

    title = Column(String(255), nullable=False)
    url_or_identifier = Column(String(500), nullable=True)  # URL, ISBN, or YouTube Video ID
    author_or_channel = Column(String(255), nullable=True)

    # Accessibility and Grounding Guarantees
    is_content_accessible = Column(Boolean, nullable=False, default=True)
    # preview_type: 'full_text', 'snippet', 'metadata_only', 'transcript'
    preview_type = Column(String(50), nullable=False, default="snippet")
    accessible_text_length = Column(Float, nullable=False, default=0.0)
    
    # Excerpt or transcript text available for factual grounding
    extracted_content = Column(Text, nullable=True)
    key_takeaways = Column(Text, nullable=True)
    relevance_score = Column(Float, nullable=False, default=1.0)
    
    # Explicit disclosure note for reviewers (e.g., "Google Books: metadata only, no full preview")
    verification_scope_note = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    lesson = relationship("Lesson", back_populates="sources")
