import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.lesson import Lesson
from app.models.lesson_revision import LessonRevision
from app.models.factual_qc import FactualQCReport
from app.models.instructional_qc import InstructionalQCReport
from app.models.generation_task import GenerationTask
from app.models.research_source import ResearchSource
from app.schemas.lesson import (
    LessonCreateRequest,
    LessonUpdateRequest,
    LessonSummary,
    LessonDetail,
    LessonGenerateRequest,
    LessonRevisionResponse
)
from app.services.llm.lesson_generator import LessonGenerationService
from app.services.export.export_service import ExportService

router = APIRouter()
generator_service = LessonGenerationService()
export_service = ExportService()


async def _run_generation_task(lesson_id: str, task_id: str):
    """Background task runner with dedicated database session."""
    db = SessionLocal()
    try:
        await generator_service.generate_lesson_pipeline(lesson_id, task_id, db)
    finally:
        db.close()


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, tags=["Lessons"])
def start_lesson_generation(
    payload: LessonGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Trigger research-grounded structured lesson generation with Google Gemini.
    Returns task_id for live progress tracking.
    """
    lesson_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    # 1. Initialize Lesson draft record
    new_lesson = Lesson(
        id=lesson_id,
        title=payload.title,
        learning_objectives=payload.learning_objectives,
        target_audience=payload.target_audience,
        difficulty_level=payload.difficulty_level,
        estimated_duration_mins=payload.estimated_duration_mins,
        status="DRAFT",
        current_version=1,
        content_blocks={}
    )
    db.add(new_lesson)

    # 2. Initialize persistent GenerationTask record
    task = GenerationTask(
        id=task_id,
        lesson_id=lesson_id,
        task_type="lesson_generation",
        status="INITIALIZING",
        current_step="Validating parameters and queued for synthesis",
        progress_percent=5,
        step_logs=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": "INITIALIZING",
            "message": f"Queued generation for '{payload.title}'"
        }]
    )
    db.add(task)
    db.commit()

    # 3. Schedule async execution
    background_tasks.add_task(_run_generation_task, lesson_id, task_id)

    return {
        "status": "ACCEPTED",
        "task_id": task_id,
        "lesson_id": lesson_id,
        "message": f"Lesson generation pipeline started for '{payload.title}'."
    }


@router.get("", response_model=List[LessonSummary], tags=["Lessons"])
def list_lessons(db: Session = Depends(get_db)):
    """List all saved lessons with current version, QC scores, and stale status."""
    lessons = db.query(Lesson).order_by(Lesson.updated_at.desc()).all()
    results = []
    
    for l in lessons:
        latest_fact = (
            db.query(FactualQCReport)
            .filter(FactualQCReport.lesson_id == l.id)
            .order_by(FactualQCReport.generated_at.desc())
            .first()
        )
        latest_inst = (
            db.query(InstructionalQCReport)
            .filter(InstructionalQCReport.lesson_id == l.id)
            .order_by(InstructionalQCReport.generated_at.desc())
            .first()
        )
        
        is_stale = False
        if latest_fact and latest_fact.is_stale:
            is_stale = True
        if latest_inst and latest_inst.is_stale:
            is_stale = True

        results.append(
            LessonSummary(
                id=l.id,
                title=l.title,
                target_audience=l.target_audience,
                difficulty_level=l.difficulty_level,
                estimated_duration_mins=l.estimated_duration_mins,
                status=l.status,
                current_version=l.current_version,
                created_at=l.created_at,
                updated_at=l.updated_at,
                factual_score=latest_fact.factual_accuracy_score if latest_fact else None,
                pedagogical_score=latest_inst.pedagogical_score if latest_inst else None,
                is_qc_stale=is_stale
            )
        )
    return results


@router.post("", response_model=LessonDetail, status_code=status.HTTP_201_CREATED, tags=["Lessons"])
def create_lesson_draft(payload: LessonCreateRequest, db: Session = Depends(get_db)):
    """Create a new manual lesson draft."""
    new_lesson = Lesson(
        id=str(uuid.uuid4()),
        title=payload.title,
        learning_objectives=payload.learning_objectives,
        target_audience=payload.target_audience,
        difficulty_level=payload.difficulty_level,
        estimated_duration_mins=payload.estimated_duration_mins,
        status="DRAFT",
        current_version=1,
        content_blocks={
            "overview": f"Overview for {payload.title}",
            "learning_objectives": payload.learning_objectives,
            "core_concepts": []
        }
    )
    db.add(new_lesson)
    db.commit()
    db.refresh(new_lesson)
    return new_lesson


@router.get("/{lesson_id}", response_model=LessonDetail, tags=["Lessons"])
def get_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieve full lesson details by ID."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return lesson


@router.put("/{lesson_id}", response_model=LessonDetail, tags=["Lessons"])
def update_lesson(lesson_id: str, payload: LessonUpdateRequest, db: Session = Depends(get_db)):
    """Update lesson content."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if payload.title is not None:
        lesson.title = payload.title
    if payload.learning_objectives is not None:
        lesson.learning_objectives = payload.learning_objectives
    if payload.target_audience is not None:
        lesson.target_audience = payload.target_audience
    if payload.difficulty_level is not None:
        lesson.difficulty_level = payload.difficulty_level
    if payload.estimated_duration_mins is not None:
        lesson.estimated_duration_mins = payload.estimated_duration_mins
    if payload.content_blocks is not None:
        lesson.content_blocks = payload.content_blocks

    lesson.current_version += 1
    lesson.status = "EDITED_PENDING_QC"
    lesson.updated_at = datetime.now(timezone.utc)

    # 1. Snapshot revision
    revision = LessonRevision(
        id=str(uuid.uuid4()),
        lesson_id=lesson.id,
        revision_number=lesson.current_version,
        content_blocks=lesson.content_blocks,
        editor_notes=payload.editor_notes or "Instructor edited lesson blocks"
    )
    db.add(revision)

    # 2. Invalidate QC reports (Requirement 6: Revision Management)
    factual_reports = db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).all()
    for report in factual_reports:
        report.is_stale = True
        report.stale_reason = f"Lesson edited to version {lesson.current_version}. Fresh verification required."

    instructional_reports = db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).all()
    for report in instructional_reports:
        report.is_stale = True
        report.stale_reason = f"Lesson edited to version {lesson.current_version}. Fresh evaluation required."

    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Lessons"])
def delete_lesson(lesson_id: str, db: Session = Depends(get_db)):
    """Delete a lesson and all dependent entities."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    db.delete(lesson)
    db.commit()
    return None


@router.get("/{lesson_id}/revisions", response_model=List[LessonRevisionResponse], tags=["Lessons"])
def get_lesson_revisions(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieve full revision history and editor snapshots for a lesson."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    revisions = (
        db.query(LessonRevision)
        .filter(LessonRevision.lesson_id == lesson_id)
        .order_by(LessonRevision.revision_number.desc())
        .all()
    )
    return revisions


@router.get("/{lesson_id}/export/json", tags=["Export"])
def export_lesson_json(lesson_id: str, db: Session = Depends(get_db)):
    """Export complete lesson package with research sources and dual QC findings as JSON."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    sources = db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).order_by(ResearchSource.citation_tag.asc()).all()
    factual_qc = db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).order_by(FactualQCReport.generated_at.desc()).first()
    instructional_qc = db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).order_by(InstructionalQCReport.generated_at.desc()).first()

    return export_service.export_json(lesson, sources, factual_qc, instructional_qc)


@router.get("/{lesson_id}/export/pdf", tags=["Export"])
def export_lesson_pdf(lesson_id: str, db: Session = Depends(get_db)):
    """Export complete lesson package with research sources and dual QC findings as PDF."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    sources = db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).order_by(ResearchSource.citation_tag.asc()).all()
    factual_qc = db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).order_by(FactualQCReport.generated_at.desc()).first()
    instructional_qc = db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).order_by(InstructionalQCReport.generated_at.desc()).first()

    pdf_buffer = export_service.export_pdf(lesson, sources, factual_qc, instructional_qc)
    filename = f"LearnForge_{lesson.title.replace(' ', '_')[:30]}_v{lesson.current_version}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{lesson_id}/export/docx", tags=["Export"])
def export_lesson_docx(lesson_id: str, db: Session = Depends(get_db)):
    """Export complete lesson package with research sources and dual QC findings as Microsoft Word DOCX."""
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    sources = db.query(ResearchSource).filter(ResearchSource.lesson_id == lesson_id).order_by(ResearchSource.citation_tag.asc()).all()
    factual_qc = db.query(FactualQCReport).filter(FactualQCReport.lesson_id == lesson_id).order_by(FactualQCReport.generated_at.desc()).first()
    instructional_qc = db.query(InstructionalQCReport).filter(InstructionalQCReport.lesson_id == lesson_id).order_by(InstructionalQCReport.generated_at.desc()).first()

    docx_buffer = export_service.export_docx(lesson, sources, factual_qc, instructional_qc)
    filename = f"LearnForge_{lesson.title.replace(' ', '_')[:30]}_v{lesson.current_version}.docx"
    return StreamingResponse(
        docx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

