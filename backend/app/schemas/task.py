from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class TaskLogEntry(BaseModel):
    timestamp: str
    stage: str
    message: str


class TaskResponse(BaseModel):
    id: str
    lesson_id: Optional[str] = None
    task_type: str
    status: str
    current_step: str
    progress_percent: int
    error_message: Optional[str] = None
    step_logs: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
