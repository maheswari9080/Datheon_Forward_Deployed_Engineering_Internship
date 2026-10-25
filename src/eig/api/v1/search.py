"""Authorized document search endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from eig.core.security import UserIdentity, get_current_user
from eig.api.v1.ingestion import default_vector_store, default_embedding_provider
from eig.rag.hybrid_retriever import HybridRetriever

search_router = APIRouter(prefix="/search", tags=["Vector & Metadata Search"])
hybrid_retriever = HybridRetriever(
    vector_store=default_vector_store,
    embedding_provider=default_embedding_provider
)


@search_router.get("/documents", summary="Authorized Hybrid Search")
async def search_documents(
    q: str = Query(..., min_length=2, description="Search query string"),
    top_k: int = Query(default=5, ge=1, le=20),
    user: UserIdentity = Depends(get_current_user)
):
    """
    Search indexed knowledge base enforcing tenant isolation and department RBAC.
    """
    results = hybrid_retriever.search_hybrid(query=q, user=user, top_k=top_k)
    return [
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "source_filename": chunk.source_filename,
            "department": chunk.department,
            "page_number": chunk.page_number,
            "row_number": chunk.row_number,
            "section_header": chunk.section_header,
            "text": chunk.text,
            "score": round(score, 4)
        }
        for chunk, score in results
    ]
