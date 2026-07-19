"""
apps/api/app/core/config.py
──────────────────────────
Centralised settings loaded from environment variables (or a .env file).
Pydantic-Settings validates all values at startup and gives clear error
messages if something required is missing.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide configuration.

    All values can be overridden via environment variables or a .env file
    at the repo root.  Defaults are safe for local Docker Compose usage.
    """

    model_config = SettingsConfigDict(
        env_file="../../../.env",  # relative to the running process; Docker sets vars directly
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ───────────────────────────────────────────────────────────────
    environment: str = "development"
    api_port: int = 8000

    # ── PostgreSQL ────────────────────────────────────────────────────────────
    database_url: PostgresDsn = PostgresDsn(
        "postgresql+psycopg://openuni:openuni@postgres:5432/openuni"
    )

    # ── Qdrant ────────────────────────────────────────────────────────────────
    qdrant_url: AnyHttpUrl = AnyHttpUrl("http://qdrant:6333")
    ollama_url: AnyHttpUrl = AnyHttpUrl("http://ollama:11434")
    # IMPORTANT: must stay aligned with the embedding model used by ingestion
    # (`packages/ingestion/ingestion/embeddings/ollama.py`).
    embedding_model: str = "nomic-embed-text"

    # ── Content ───────────────────────────────────────────────────────────────
    # We resolve the universities directory dynamically in case we run via uvicorn directly
    universities_dir: Path = Path(__file__).resolve().parents[4] / "universities"

    # ── Derived helpers ───────────────────────────────────────────────────────
    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got '{v}'")
        return v

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


@lru_cache
def get_settings() -> Settings:
    """Return the cached Settings singleton.

    Use this as a FastAPI dependency::

        from app.core.config import get_settings

        @app.get("/")
        def root(settings: Settings = Depends(get_settings)):
            ...
    """
    return Settings()
