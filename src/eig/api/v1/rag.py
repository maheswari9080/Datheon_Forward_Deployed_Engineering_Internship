"""Secure RAG generation endpoints."""

from fastapi import APIRouter, Depends
from eig.core.security import UserIdentity, get_current_user
from eig.api.v1.ingestion import default_vector_store, default_embedding_provider
from eig.rag.hybrid_retriever import HybridRetriever
from eig.rag.reranker import CrossEncoderReranker
from eig.rag.engine import SecureRAGEngine
from eig.rag.models import RAGQueryRequest, RAGQueryResponse
from eig.config import settings

rag_router = APIRouter(prefix="/rag", tags=["Multi-Tenant RAG"])

_retriever = HybridRetriever(
    vector_store=default_vector_store,
    embedding_provider=default_embedding_provider
)
_reranker = CrossEncoderReranker(model_name=settings.RERANKER_MODEL_NAME)
secure_rag_engine = SecureRAGEngine(
    retriever=_retriever,
    reranker=_reranker,
    score_threshold=settings.RETRIEVAL_SCORE_THRESHOLD
)


@rag_router.post("/query", response_model=RAGQueryResponse, summary="Execute Grounded RAG Query")
async def execute_rag_query(
    request: RAGQueryRequest,
    user: UserIdentity = Depends(get_current_user)
):
    """
    Execute grounded RAG query with server-verified tenant isolation,
    cross-encoder reranking, and explicit page-level citations.
    """
    return await secure_rag_engine.answer_query(request=request, user=user)
