from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.generation_task import GenerationTask
from app.schemas.task import TaskResponse

router = APIRouter()


@router.get("/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task_status(task_id: str, db: Session = Depends(get_db)):
    """Retrieve the persistent state and step logs of a background task."""
    task = db.query(GenerationTask).filter(GenerationTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("", response_model=List[TaskResponse], tags=["Tasks"])
def list_tasks(limit: int = 20, db: Session = Depends(get_db)):
    """List recent persistent background tasks."""
    return db.query(GenerationTask).order_by(GenerationTask.created_at.desc()).limit(limit).all()
