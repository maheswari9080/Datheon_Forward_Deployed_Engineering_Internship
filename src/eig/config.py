"""Application configuration and environment variable management using Pydantic v2."""

import os
from typing import Literal, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Enterprise Intelligence Gateway runtime settings."""

    # Application Information
    APP_NAME: str = "Enterprise Intelligence Gateway"
    VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # Security & Cryptography
    SECRET_KEY: str = Field(
        default="eig-enterprise-secret-key-32-bytes-minimum-security-entropy-sample",
        description="Key used for cryptographic JWT signing and session validation"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APPROVAL_HMAC_SECRET: str = Field(
        default="eig-hmac-approval-secret-key-high-entropy-production-guardrail",
        description="Key used for HMAC signing of approval requests"
    )
    APPROVAL_TTL_SECONDS: int = 300  # 5 minutes

    # Database Configuration
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./data/eig.db",
        description="SQLAlchemy async database URI"
    )

    # Vector Storage
    VECTOR_STORE_PROVIDER: Literal["chroma", "qdrant"] = "chroma"
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "eig_enterprise_knowledge"
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = "eig_enterprise_knowledge"

    # Embedding Providers
    EMBEDDING_PROVIDER: Literal["local", "mock"] = "mock"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384

    # Reranker Configuration
    RERANKER_PROVIDER: Literal["local", "mock", "none"] = "mock"
    RERANKER_MODEL_NAME: str = "bge-reranker-base"

    # Ingestion Constraints & Defaults
    MAX_FILE_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB
    MAX_BATCH_DOCUMENTS: int = 100
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 60

    # RAG Retrieval & Context Budgeting
    MAX_RETRIEVAL_CANDIDATES: int = 20
    MAX_CONTEXT_CHUNKS: int = 5
    RETRIEVAL_SCORE_THRESHOLD: float = 0.25
    CONTEXT_BUDGET_TOKENS: int = 4000

    # Rate Limiting & Operations
    RATE_LIMIT_PER_MINUTE: int = 120
    CIRCUIT_BREAKER_FAIL_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def safe_diagnostics(self) -> Dict[str, Any]:
        """Return operational configuration with all secrets strictly redacted."""
        return {
            "app_name": self.APP_NAME,
            "version": self.VERSION,
            "environment": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "api_prefix": self.API_V1_STR,
            "vector_store_provider": self.VECTOR_STORE_PROVIDER,
            "chroma_collection": self.CHROMA_COLLECTION_NAME,
            "embedding_provider": self.EMBEDDING_PROVIDER,
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "reranker_provider": self.RERANKER_PROVIDER,
            "max_file_size_mb": self.MAX_FILE_SIZE_BYTES / (1024 * 1024),
            "max_batch_documents": self.MAX_BATCH_DOCUMENTS,
            "default_chunk_size": self.DEFAULT_CHUNK_SIZE,
            "default_chunk_overlap": self.DEFAULT_CHUNK_OVERLAP,
            "approval_ttl_seconds": self.APPROVAL_TTL_SECONDS,
            "secret_key": "***REDACTED***",
            "approval_hmac_secret": "***REDACTED***",
            "database_url": self.DATABASE_URL.split("@")[-1] if "@" in self.DATABASE_URL else "sqlite:///data/eig.db",
        }


# Global singleton instance
settings = Settings()
