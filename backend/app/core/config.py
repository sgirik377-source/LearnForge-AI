import os
from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field

# Base directories
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Search candidates for .env file
ENV_CANDIDATES = [
    BACKEND_DIR / ".env",
    ROOT_DIR / ".env",
    Path(".env"),
    Path("backend/.env")
]

EXISTING_ENV_FILES = [str(p) for p in ENV_CANDIDATES if p.is_file()]


def get_gemini_api_key() -> str:
    """
    Centrally and dynamically resolves the Gemini API key.
    Checks:
      1. Live os.environ
      2. Settings.GEMINI_API_KEY
      3. backend/.env and root .env directly on disk
    Never exposes or logs the key.
    """
    # 1. Live os.environ
    env_val = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_val:
        return env_val

    # 2. Pre-loaded settings instance (if already instantiated)
    try:
        if "settings" in globals():
            s_val = getattr(globals()["settings"], "GEMINI_API_KEY", "").strip()
            if s_val:
                return s_val
    except Exception:
        pass

    # 3. Direct disk read of .env files (handles edits made after process startup)
    for env_path in ENV_CANDIDATES:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception:
                pass

    return ""


def get_gemini_model() -> str:
    """Resolves Gemini model name centrally with fallback to gemini-2.5-flash."""
    env_val = os.environ.get("GEMINI_MODEL", "").strip()
    if env_val:
        return env_val
    for env_path in ENV_CANDIDATES:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GEMINI_MODEL=") and not line.startswith("#"):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception:
                pass
    return "gemini-2.5-flash"


class Settings(BaseSettings):
    APP_NAME: str = "LearnForge AI"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./learnforge.db"
    GEMINI_API_KEY: str = Field(default_factory=get_gemini_api_key)
    GEMINI_MODEL: str = Field(default_factory=get_gemini_model)
    GOOGLE_BOOKS_API_KEY: str = Field(default="", env="GOOGLE_BOOKS_API_KEY")
    YOUTUBE_API_KEY: str = Field(default="", env="YOUTUBE_API_KEY")
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000"
    ]

    class Config:
        env_file = EXISTING_ENV_FILES or ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
