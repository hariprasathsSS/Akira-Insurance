"""AKIRA INSURANCE — Application settings using pydantic-settings."""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "AKIRA_INSURANCE"
    API_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    DEMO_AUTH_ENABLED: bool = False
    APP_SECRET_KEY: str = "change-this-in-production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://akira:change-me@localhost:5432/akira"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "akira_policy_chunks"

    # File storage
    UPLOAD_DIR: str = "/app/storage/policies"
    MAX_UPLOAD_MB: int = 15
    ALLOWED_UPLOAD_MIME_TYPES: str = "application/pdf"

    # LLM
    LLM_PROVIDER: Optional[str] = None  # "openai" | "google"
    LLM_MODEL: Optional[str] = None
    LLM_API_KEY: Optional[str] = None

    # Embeddings
    EMBEDDING_PROVIDER: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_DIM: int = 1536
    VECTOR_SIZE: Optional[int] = None

    # Chunking
    CHUNK_SIZE: int = 700
    CHUNK_OVERLAP_SIZE: int = 100

    # Langfuse
    LANGFUSE_HOST: str = "http://localhost:3000"
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_ENABLED: bool = True

    # Business rules
    STP_THRESHOLD_INR: int = 10000
    MAX_CHAT_MESSAGE_CHARS: int = 8000
    RAG_TOP_K: int = 8
    RAG_MIN_SCORE: float = 0.3

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def demo_auth_active(self) -> bool:
        return self.is_development and self.DEMO_AUTH_ENABLED

    @property
    def llm_configured(self) -> bool:
        return bool(self.LLM_PROVIDER and self.LLM_API_KEY)

    @property
    def effective_embedding_dim(self) -> int:
        return self.VECTOR_SIZE or self.EMBEDDING_DIM

    @property
    def embedding_configured(self) -> bool:
        if not self.EMBEDDING_PROVIDER:
            return False
        provider = self.EMBEDDING_PROVIDER.lower()
        if provider in ("sentence_transformers", "sentence-transformers", "fastembed", "huggingface"):
            return bool(self.EMBEDDING_MODEL)
        return bool(self.EMBEDDING_API_KEY)

    @property
    def langfuse_configured(self) -> bool:
        return bool(
            self.LANGFUSE_ENABLED
            and self.LANGFUSE_PUBLIC_KEY
            and self.LANGFUSE_SECRET_KEY
        )

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @model_validator(mode="after")
    def validate_demo_auth_env(self) -> "Settings":
        if self.DEMO_AUTH_ENABLED and self.APP_ENV != "development":
            raise ValueError(
                "DEMO_AUTH_ENABLED=true is only allowed when APP_ENV=development. "
                "This mock identity is not suitable for production."
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
