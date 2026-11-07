import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.lesson import Lesson
from app.models.factual_qc import FactualQCReport
from app.models.instructional_qc import InstructionalQCReport
from app.schemas.qc import (
    FactualQCReportResponse,
    InstructionalQCReportResponse,
    DualQCResponse,
    QCSummaryResponse
)
from app.services.qc.factual_qc_service import FactualQCService
from app.services.qc.instructional_qc_service import InstructionalQCService

logger = logging.getLogger(__name__)

router = APIRouter()
factual_qc_service = FactualQCService()
instructional_qc_service = InstructionalQCService()


@router.post("/{lesson_id}/factual", response_model=FactualQCReportResponse, tags=["Quality Control"])
async def run_factual_qc(lesson_id: str, db: Session = Depends(get_db)):
    """
    Run independent Factual & Research Accuracy Quality Control.
    Extracts claims, verifies against accessible research excerpts, audits citations,
    and computes explicit rubric scores.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if not lesson.content_blocks:
        raise HTTPException(
            status_code=400,
            detail="Cannot run QC on an ungenerated lesson. Please generate lesson content first."
        )

    try:
        report = await factual_qc_service.evaluate_lesson(lesson_id, db)
        return report
    except Exception as e:
        logger.error(f"Factual QC execution failed for {lesson_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Factual QC failed: {str(e)}")


@router.get("/{lesson_id}/factual", response_model=FactualQCReportResponse, tags=["Quality Control"])
def get_factual_qc(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieve the latest Factual & Research Accuracy QC report for a lesson."""
    report = (
        db.query(FactualQCReport)
        .filter(FactualQCReport.lesson_id == lesson_id)
        .order_by(FactualQCReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Factual QC report not found for this lesson")
    return report


@router.post("/{lesson_id}/instructional", response_model=InstructionalQCReportResponse, tags=["Quality Control"])
async def run_instructional_qc(lesson_id: str, db: Session = Depends(get_db)):
    """
    Run independent Instructional Design & Pedagogical Quality Control.
    Evaluates objective alignment, cognitive scaffolding, Bloom's taxonomy,
    examples, assessments, and duration pacing.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if not lesson.content_blocks:
        raise HTTPException(
            status_code=400,
            detail="Cannot run QC on an ungenerated lesson. Please generate lesson content first."
        )

    try:
        report = await instructional_qc_service.evaluate_lesson(lesson_id, db)
        return report
    except Exception as e:
        logger.error(f"Instructional QC execution failed for {lesson_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Instructional QC failed: {str(e)}")


@router.get("/{lesson_id}/instructional", response_model=InstructionalQCReportResponse, tags=["Quality Control"])
def get_instructional_qc(lesson_id: str, db: Session = Depends(get_db)):
    """Retrieve the latest Instructional Design & Pedagogical QC report for a lesson."""
    report = (
        db.query(InstructionalQCReport)
        .filter(InstructionalQCReport.lesson_id == lesson_id)
        .order_by(InstructionalQCReport.generated_at.desc())
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Instructional QC report not found for this lesson")
    return report


@router.post("/{lesson_id}/all", response_model=DualQCResponse, tags=["Quality Control"])
async def run_dual_qc(lesson_id: str, db: Session = Depends(get_db)):
    """
    Execute both QC engines independently for a lesson.
    Neither engine's score influences the other.
    Failure in one engine is isolated and does not prevent the other from completing.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    if not lesson.content_blocks:
        raise HTTPException(
            status_code=400,
            detail="Cannot run QC on an ungenerated lesson. Please generate lesson content first."
        )

    factual_report = None
    instructional_report = None
    errors = []

    # 1. Independent Factual QC Run
    try:
        factual_report = await factual_qc_service.evaluate_lesson(lesson_id, db)
    except Exception as e:
        logger.error(f"Factual QC failed during dual run for {lesson_id}: {e}")
        errors.append(f"Factual QC error: {str(e)}")

    # 2. Independent Instructional QC Run
    try:
        instructional_report = await instructional_qc_service.evaluate_lesson(lesson_id, db)
    except Exception as e:
        logger.error(f"Instructional QC failed during dual run for {lesson_id}: {e}")
        errors.append(f"Instructional QC error: {str(e)}")

    if not factual_report and not instructional_report:
        raise HTTPException(
            status_code=500,
            detail=f"Both QC engines failed: {'; '.join(errors)}"
        )

    # If both passed without stale flags, update lesson status
    if factual_report and instructional_report:
        if factual_report.status == "PASSED" and instructional_report.status == "PASSED":
            lesson.status = "REVIEWED"
        else:
            lesson.status = "NEEDS_REVISION"
        db.commit()

    msg = "Both QC evaluations completed." if not errors else f"Completed with partial errors: {'; '.join(errors)}"
    return DualQCResponse(
        status="COMPLETED" if not errors else "PARTIAL",
        message=msg,
        factual_qc=factual_report,
        instructional_qc=instructional_report
    )


@router.get("/{lesson_id}/summary", response_model=QCSummaryResponse, tags=["Quality Control"])
def get_qc_summary(lesson_id: str, db: Session = Depends(get_db)):
    """
    Retrieve unified summary of latest Factual and Instructional QC reports,
    including staleness detection.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    factual = (
        db.query(FactualQCReport)
        .filter(FactualQCReport.lesson_id == lesson_id)
        .order_by(FactualQCReport.generated_at.desc())
        .first()
    )
    instructional = (
        db.query(InstructionalQCReport)
        .filter(InstructionalQCReport.lesson_id == lesson_id)
        .order_by(InstructionalQCReport.generated_at.desc())
        .first()
    )

    is_stale = False
    stale_reason = None

    if factual and factual.is_stale:
        is_stale = True
        stale_reason = factual.stale_reason
    elif instructional and instructional.is_stale:
        is_stale = True
        stale_reason = instructional.stale_reason

    return QCSummaryResponse(
        lesson_id=lesson.id,
        lesson_version=lesson.current_version,
        is_stale=is_stale,
        stale_reason=stale_reason,
        factual_qc=factual,
        instructional_qc=instructional
    )
