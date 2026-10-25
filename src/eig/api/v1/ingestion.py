"""Document ingestion and registry REST endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from eig.core.database import get_db, DocumentRegistryModel
from eig.core.security import UserIdentity, get_current_user
from eig.ingestion.pipeline import IngestionPipeline
from eig.ingestion.models import IngestionReport
from eig.ingestion.embeddings.local_provider import LocalEmbeddingProvider
from eig.ingestion.vector_store.chroma_store import ChromaVectorStore
from eig.config import settings

ingestion_router = APIRouter(prefix="/ingest", tags=["Document Ingestion & ETL"])

# Global singleton pipeline instance
default_vector_store = ChromaVectorStore(
    persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
    collection_name=settings.CHROMA_COLLECTION_NAME
)
default_embedding_provider = LocalEmbeddingProvider(
    model_name=settings.EMBEDDING_MODEL_NAME,
    dimension=settings.EMBEDDING_DIMENSION
)
ingestion_pipeline = IngestionPipeline(
    vector_store=default_vector_store,
    embedding_provider=default_embedding_provider,
    chunk_size=settings.DEFAULT_CHUNK_SIZE,
    chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP
)


@ingestion_router.post("/upload", summary="Ingest Document File")
async def upload_document(
    file: UploadFile = File(...),
    department: str = Form(...),
    access_tier: int = Form(default=1),
    document_date: Optional[str] = Form(default=None),
    force_reindex: bool = Form(default=False),
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest a PDF, CSV, or Markdown file with strict tenant and RBAC metadata tagging.
    Tenant is strictly derived from user identity context.
    """
    if not user.can_access_department(department):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"User not authorized to ingest documents into department: {department}"
        )

    content = await file.read()
    filename = file.filename or "uploaded_document"

    try:
        doc_id, chunk_cnt, is_dup = await ingestion_pipeline.ingest_single_document(
            session=db,
            content_bytes=content,
            filename=filename,
            tenant_id=user.tenant_id,
            department=department,
            access_tier=access_tier,
            document_date=document_date,
            force_reindex=force_reindex
        )
        return {
            "document_id": doc_id,
            "filename": filename,
            "tenant_id": user.tenant_id,
            "department": department,
            "access_tier": access_tier,
            "chunks_indexed": chunk_cnt,
            "is_duplicate": is_dup,
            "status": "INDEXED"
        }
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@ingestion_router.get("/documents", summary="List Ingested Documents")
async def list_documents(
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all authorized indexed documents within caller's tenant boundary."""
    stmt = select(DocumentRegistryModel).where(
        DocumentRegistryModel.tenant_id == user.tenant_id,
        DocumentRegistryModel.status != "DELETED",
        DocumentRegistryModel.access_tier <= user.clearance_level
    )
    res = await db.execute(stmt)
    docs = res.scalars().all()
    # Filter by user departments if not admin
    if "admin" not in user.roles:
        docs = [d for d in docs if user.can_access_department(d.department)]

    return [
        {
            "id": d.id,
            "filename": d.source_filename,
            "department": d.department,
            "access_tier": d.access_tier,
            "document_date": d.document_date,
            "total_chunks": d.total_chunks,
            "created_at": d.created_at.isoformat()
        }
        for d in docs
    ]


@ingestion_router.delete("/documents/{document_id}", summary="Delete Document")
async def delete_document(
    document_id: str,
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Purge document chunks from vector index and registry."""
    success = await ingestion_pipeline.delete_document(
        session=db,
        tenant_id=user.tenant_id,
        document_id=document_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found in tenant {user.tenant_id}."
        )
    return {"status": "DELETED", "document_id": document_id}
