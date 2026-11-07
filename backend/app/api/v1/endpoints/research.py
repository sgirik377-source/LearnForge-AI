import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lesson import Lesson
from app.models.research_source import ResearchSource
from app.models.generation_task import GenerationTask
from app.schemas.research import ResearchSourceResponse, ResearchSourceCreate
from app.services.research.aggregator import ResearchAggregator

router = APIRouter()
aggregator = ResearchAggregator()


@router.get("/{lesson_id}/sources", response_model=List[ResearchSourceResponse], tags=["Research"])
def get_lesson_sources(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieve all external research sources and their accessibility guarantees for a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    sources = (
        db.query(ResearchSource)
        .filter(ResearchSource.lesson_id == lesson_id)
        .order_by(ResearchSource.citation_tag.asc())
        .all()
    )
    return sources


@router.post("/{lesson_id}/harvest", tags=["Research"])
async def harvest_research_for_lesson(
    lesson_id: str,
    max_per_provider: int = 3,
    db: Session = Depends(get_db)
):
    """
    Execute multimodal research harvesting across Web, Google Books, and YouTube.
    Persists task progress and saves normalized sources in SQLite.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # 1. Initialize persistent task record
    task = GenerationTask(
        id=str(uuid.uuid4()),
        lesson_id=lesson.id,
        task_type="research_harvest",
        status="RESEARCHING",
        current_step=f"Querying Web, Books, and YouTube for '{lesson.title}'",
        progress_percent=20,
        step_logs=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "research_start",
            "message": f"Initiating research harvest for '{lesson.title}'"
        }]
    )
    db.add(task)
    db.commit()

    try:
        # 2. Run multimodal aggregator
        harvest_result = await aggregator.harvest(
            query=lesson.title,
            learning_objectives=lesson.learning_objectives,
            max_per_provider=max_per_provider
        )

        sources_data = harvest_result["sources"]
        provider_errors = harvest_result.get("provider_errors", {})

        # 3. Persist to SQLite
        saved_records = aggregator.persist_sources(
            lesson_id=lesson.id,
            sources=sources_data,
            db=db,
            replace_existing=True
        )

        # 4. Update task completion
        task.status = "COMPLETED"
        task.current_step = (
            f"Retrieved {len(saved_records)} sources "
            f"({harvest_result['accessible_count']} accessible, {harvest_result['metadata_only_count']} metadata-only)"
        )
        task.progress_percent = 100
        task.step_logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "research_complete",
            "message": task.current_step,
            "provider_errors": provider_errors
        })
        db.commit()

        return {
            "status": "success",
            "task_id": task.id,
            "total_harvested": len(saved_records),
            "accessible_count": harvest_result["accessible_count"],
            "metadata_only_count": harvest_result["metadata_only_count"],
            "provider_errors": provider_errors,
            "sources": [ResearchSourceResponse.model_validate(r) for r in saved_records]
        }

    except Exception as e:
        task.status = "FAILED"
        task.error_message = str(e)
        task.current_step = "Research harvest encountered an unexpected failure"
        task.step_logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "error",
            "message": str(e)
        })
        db.commit()
        raise HTTPException(status_code=500, detail=f"Research harvest failed: {str(e)}")


@router.post("/{lesson_id}/sources", response_model=ResearchSourceResponse, status_code=status.HTTP_201_CREATED, tags=["Research"])
def add_custom_source(
    lesson_id: str,
    payload: ResearchSourceCreate,
    db: Session = Depends(get_db)
):
    """Add a custom verified source manually."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    count = db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).count()
    citation_tag = f"[REF-{count + 1}]"

    new_source = ResearchSource(
        id=str(uuid.uuid4()),
        lesson_id=lesson.id,
        source_type=payload.source_type,
        citation_tag=citation_tag,
        title=payload.title,
        url_or_identifier=payload.url_or_identifier,
        author_or_channel=payload.author_or_channel,
        is_content_accessible=payload.is_content_accessible,
        preview_type=payload.preview_type,
        accessible_text_length=float(len(payload.extracted_content or "")),
        extracted_content=payload.extracted_content,
        key_takeaways=payload.key_takeaways,
        relevance_score=1.0,
        verification_scope_note=payload.verification_scope_note or "Manual instructor verified source."
    )
    db.add(new_source)
    db.commit()
    db.refresh(new_source)
    return new_source


@router.delete("/{lesson_id}/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Research"])
def delete_source(lesson_id: str, source_id: str, db: Session = Depends(get_db)):
    """Delete a research source."""
    source = db.query(ResearchSource).filter(
        ResearchSource.lesson_id == lesson_id,
        ResearchSource.id == source_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    db.delete(source)
    db.commit()
    return None
