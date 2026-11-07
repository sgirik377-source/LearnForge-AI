from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
import app.models  # Ensures all models are registered with Base.metadata
from app.api.v1.api_router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure all database tables are created in SQLite
    Base.metadata.create_all(bind=engine)
    yield
    # Teardown logic if needed in future


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Professional AI-Powered Lesson Creation & Quality Assurance Platform",
    lifespan=lifespan
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }
