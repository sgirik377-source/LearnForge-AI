from fastapi import APIRouter
from app.api.v1.endpoints import health, lessons, tasks, qc, research

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(lessons.router, prefix="/lessons")
api_router.include_router(tasks.router, prefix="/tasks")
api_router.include_router(qc.router, prefix="/qc")
api_router.include_router(research.router, prefix="/research")
