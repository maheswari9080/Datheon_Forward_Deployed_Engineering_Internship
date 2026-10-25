"""Pydantic schemas and metadata contracts for document ingestion and chunking."""

import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Core document metadata required across all ingestion formats."""
    tenant_id: str = Field(..., description="Enterprise tenant boundary")
    document_id: str = Field(..., description="Unique document ID (hash or UUID)")
    source_filename: str = Field(..., description="Original filename uploaded")
    department: str = Field(..., description="Owning business department")
    access_tier: int = Field(default=1, ge=1, le=5, description="Clearance level required")
    document_date: Optional[str] = Field(
        default=None,
        description="Explicit document date (YYYY-MM-DD) or None if absent"
    )
    content_hash: str = Field(..., description="SHA-256 hash of raw file content")
    ingestion_timestamp: str = Field(
        default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
        description="ISO 8601 ingestion timestamp"
    )
    parser_version: str = Field(default="1.0.0", description="Parser version applied")


class ExtractedSection(BaseModel):
    """Intermediate parsed text unit with provenance markers."""
    text: str
    page_number: Optional[int] = None
    row_number: Optional[int] = None
    section_header: Optional[str] = None
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """Semantic or structure-aware chunk indexed into vector storage."""
    chunk_id: str = Field(..., description="Composite ID: {document_id}_{chunk_index}")
    document_id: str
    tenant_id: str
    text: str
    page_number: Optional[int] = None
    row_number: Optional[int] = None
    section_header: Optional[str] = None
    department: str
    access_tier: int
    document_date: Optional[str] = None
    source_filename: str
    content_hash: str
    chunk_index: int
    embedding: Optional[List[float]] = None

    def to_metadata_dict(self) -> Dict[str, Any]:
        """Convert chunk metadata to flat dictionary for vector DB payload indexing."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "page_number": self.page_number if self.page_number is not None else -1,
            "row_number": self.row_number if self.row_number is not None else -1,
            "section_header": self.section_header or "",
            "department": self.department,
            "access_tier": self.access_tier,
            "document_date": self.document_date or "UNAVAILABLE",
            "source_filename": self.source_filename,
            "content_hash": self.content_hash,
            "chunk_index": self.chunk_index,
        }


class IngestionItemError(BaseModel):
    """Error details for partial batch ingestion failures."""
    filename: str
    error_type: str
    detail: str


class IngestionReport(BaseModel):
    """Standardized batch or single document ingestion report."""
    job_id: str
    tenant_id: str
    total_documents: int
    indexed_documents: int
    skipped_duplicates: int
    failed_documents: int
    total_chunks: int
    duration_seconds: float
    errors: List[IngestionItemError] = Field(default_factory=list)
    document_ids: List[str] = Field(default_factory=list)
