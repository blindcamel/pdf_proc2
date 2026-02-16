from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Info
    APP_NAME: str = "PDFProc2"
    DEBUG: bool = False
    LOG_LEVEL: str = "Info"

    # Paths
    # We use .parent.parent.parent to get back to the project root from app/core/
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    PROCESSED_DIR: Path = DATA_DIR / "processed"
    FAILED_DIR: Path = DATA_DIR / "failed"

    # Database
    DATABASE_URL: str = "sqlite:///./data/pdfproc.db"

    # AI Provider Selection
    # Change LLM_PROVIDER in .env to "anthropic" to switch
    LLM_PROVIDER: Literal["openai", "anthropic"] = "openai"

    # Cascade Model Configuration
    # Model A: Fast/Cheap (Text)
    # Model B: Smart/Expensive (Vision Fallback)
    MODEL_A_NAME: str = "gpt-4o-mini"
    MODEL_B_NAME: str = "gpt-4o"

    # API Keys (Loaded from .env)
    OPENAI_API_KEY: str | None = None

    # Processing Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


# Initialize settings
settings = Settings()


# Ensure local directories exist
def ensure_dirs():
    for path in [settings.UPLOAD_DIR, settings.PROCESSED_DIR, settings.FAILED_DIR]:
        path.mkdir(parents=True, exist_ok=True)


ensure_dirs()
