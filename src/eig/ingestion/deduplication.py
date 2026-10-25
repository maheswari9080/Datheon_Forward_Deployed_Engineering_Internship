"""SHA-256 document hashing and idempotent deduplication logic."""

import hashlib
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eig.core.database import DocumentRegistryModel


def compute_content_hash(content_bytes: bytes) -> str:
    """Compute deterministic SHA-256 checksum of raw file payload."""
    hasher = hashlib.sha256()
    hasher.update(content_bytes)
    return hasher.hexdigest()


def generate_document_id(tenant_id: str, content_hash: str) -> str:
    """Derive deterministic composite document identifier."""
    composite = f"{tenant_id}:{content_hash}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()[:24]


async def check_duplicate_document(
    session: AsyncSession,
    tenant_id: str,
    content_hash: str
) -> Tuple[bool, Optional[DocumentRegistryModel]]:
    """
    Query registry for existing document with identical content hash within tenant isolation boundary.
    Returns (is_duplicate, existing_model_or_none).
    """
    stmt = (
        select(DocumentRegistryModel)
        .where(
            DocumentRegistryModel.tenant_id == tenant_id,
            DocumentRegistryModel.content_hash == content_hash
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        return True, existing
    return False, None
