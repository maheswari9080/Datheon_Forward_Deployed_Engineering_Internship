"""Asynchronous database engine, declarative ORM models, and session management."""

import datetime
import hashlib
import json
import os
from typing import AsyncGenerator, Optional
from sqlalchemy import String, Integer, DateTime, Text, Boolean, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from eig.config import settings


class Base(DeclarativeBase):
    """Declarative base class for SQLAlchemy 2.0 ORM models."""
    pass


class DocumentRegistryModel(Base):
    """Tracks state and provenance of ingested enterprise documents."""
    __tablename__ = "document_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_filename: Mapped[str] = mapped_column(String(256), nullable=False)
    department: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    access_tier: Mapped[int] = mapped_column(Integer, default=1, index=True, nullable=False)
    document_date: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    parser_version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="INDEXED")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )


class ApprovalRecordModel(Base):
    """Tracks human-in-the-loop authorization requests for sensitive write operations."""
    __tablename__ = "approval_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    arguments_json: Mapped[str] = mapped_column(Text, nullable=False)
    hmac_token: Mapped[str] = mapped_column(String(128), nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", index=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class AuditEventModel(Base):
    """Append-only, cryptographically linked audit event log."""
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(128), nullable=False)
    resource: Mapped[str] = mapped_column(String(256), nullable=False)
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
    prev_hash: Mapped[str] = mapped_column(String(64), default="0" * 64, nullable=False)
    current_hash: Mapped[str] = mapped_column(String(64), nullable=False)


class MockStateModel(Base):
    """State storage for mock ERP/CRM entities (leads, tickets, inventory)."""
    __tablename__ = "mock_enterprise_state"

    entity_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    data_json: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False
    )


# Async Engine & Sessionmaker
# Ensure data directory exists if using sqlite
if "sqlite" in settings.DATABASE_URL:
    os.makedirs("./data", exist_ok=True)

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
