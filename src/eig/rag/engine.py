"""Fail-closed Secure RAG generation engine with verifiable citations and abstention."""

import time
from typing import List, Optional, Tuple, Dict, Any
from eig.config import settings
from eig.core.logging import logger
from eig.core.metrics import EIG_RAG_QUERIES
from eig.core.security import UserIdentity
from eig.ingestion.models import DocumentChunk
from eig.rag.models import Citation, RAGQueryRequest, RAGQueryResponse
from eig.rag.hybrid_retriever import HybridRetriever
from eig.rag.reranker import BaseReranker
from eig.rag.context_budget import ContextWindowBudgeter
from eig.rag.guardrails import detect_prompt_injection, isolate_untrusted_evidence
from eig.rag.query_rewriter import QueryRewriter


INSUFFICIENT_EVIDENCE_MESSAGE = (
    "INSUFFICIENT_EVIDENCE: The provided authorized enterprise context does not contain "
    "sufficient verified evidence to answer this question."
)


class SecureRAGEngine:
    """
    Production multi-tenant RAG engine enforcing strict RBAC, isolation, and citation grounding.
    """

    def __init__(
        self,
        retriever: HybridRetriever,
        reranker: BaseReranker,
        score_threshold: float = settings.RETRIEVAL_SCORE_THRESHOLD,
        context_budgeter: Optional[ContextWindowBudgeter] = None
    ):
        self.retriever = retriever
        self.reranker = reranker
        self.score_threshold = score_threshold
        self.context_budgeter = context_budgeter or ContextWindowBudgeter(
            max_tokens=settings.CONTEXT_BUDGET_TOKENS,
            max_chunks=settings.MAX_CONTEXT_CHUNKS
        )
        self.query_rewriter = QueryRewriter()

    def _post_retrieval_revalidate(
        self,
        chunks: List[Tuple[DocumentChunk, float]],
        user: UserIdentity
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Enforce Security Invariant #2: Revalidate authorization on retrieved chunks.
        Fail closed on any boundary mismatch.
        """
        valid_chunks: List[Tuple[DocumentChunk, float]] = []
        for chunk, score in chunks:
            # Recheck tenant isolation
            if chunk.tenant_id != user.tenant_id:
                logger.error(
                    f"CRITICAL SECURITY INVARIANT VIOLATION: Cross-tenant chunk {chunk.chunk_id} "
                    f"(tenant: {chunk.tenant_id}) retrieved for user tenant {user.tenant_id}!"
                )
                continue

            # Recheck clearance tier
            if not user.can_access_clearance(chunk.access_tier):
                logger.warning(
                    f"Access denied: chunk {chunk.chunk_id} requires tier {chunk.access_tier}, "
                    f"user clearance is {user.clearance_level}"
                )
                continue

            # Recheck department
            if not user.can_access_department(chunk.department):
                logger.warning(
                    f"Access denied: chunk {chunk.chunk_id} in department {chunk.department} "
                    f"not in user authorized departments {user.departments}"
                )
                continue

            valid_chunks.append((chunk, score))

        return valid_chunks

    def _build_grounded_answer(
        self,
        query: str,
        budgeted_chunks: List[Tuple[DocumentChunk, float]]
    ) -> Tuple[str, List[Citation]]:
        """
        Synthesize answer strictly grounded on evidence, building precise citations.
        """
        citations: List[Citation] = []
        evidence_texts = []

        for chunk, score in budgeted_chunks:
            # Build representative snippet (first 120 chars)
            snippet = chunk.text.replace("\n", " ").strip()[:140] + "..."
            citation = Citation(
                document_name=chunk.source_filename,
                page_number=chunk.page_number,
                row_number=chunk.row_number,
                section_header=chunk.section_header,
                chunk_id=chunk.chunk_id,
                snippet=snippet
            )
            citations.append(citation)

            citation_tag = citation.format_citation()
            evidence_texts.append(f"{citation_tag}\n{chunk.text}")

        # Grounded response synthesis
        combined_evidence = "\n\n".join(evidence_texts)
        answer = (
            f"Based on the authorized enterprise records:\n\n"
            f"{combined_evidence}\n\n"
            f"Sources Verified: {len(citations)} citation(s)."
        )
        return answer, citations

    async def answer_query(
        self,
        request: RAGQueryRequest,
        user: UserIdentity
    ) -> RAGQueryResponse:
        """
        Execute secure RAG query:
        Rewrite -> Hybrid Retrieve -> RBAC Revalidate -> Rerank -> Budget -> Grounded Answer.
        """
        start_time = time.time()

        # Check prompt injection on user query
        has_injection, matched = detect_prompt_injection(request.query)
        if has_injection:
            EIG_RAG_QUERIES.labels(outcome="rejected_injection").inc()
            return RAGQueryResponse(
                query=request.query,
                answer=(
                    "SECURITY_REJECTION: Query contained suspicious prompt injection or override patterns "
                    "and was blocked by policy."
                ),
                insufficient_evidence=True,
                execution_time_seconds=time.time() - start_time
            )

        # 1. Query expansion
        expanded_query = self.query_rewriter.rewrite_query(request.query)

        # 2. Hybrid Retrieval (Pre-filtered with user identity)
        raw_candidates = self.retriever.search_hybrid(
            query=expanded_query,
            user=user,
            top_k=request.top_k * 3
        )

        # 3. Post-Retrieval Revalidation (Security Invariant #2)
        valid_candidates = self._post_retrieval_revalidate(raw_candidates, user)

        if not valid_candidates:
            EIG_RAG_QUERIES.labels(outcome="insufficient_evidence").inc()
            return RAGQueryResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_MESSAGE,
                insufficient_evidence=True,
                chunks_evaluated=0,
                execution_time_seconds=time.time() - start_time
            )

        # 4. Cross-Encoder Reranking
        if request.enable_reranking:
            reranked_candidates = self.reranker.rerank(
                query=expanded_query,
                candidates=valid_candidates,
                top_n=request.top_k
            )
        else:
            reranked_candidates = valid_candidates[:request.top_k]

        # 5. Score threshold filter & abstention check
        top_score = reranked_candidates[0][1] if reranked_candidates else 0.0
        if top_score < self.score_threshold:
            logger.info(
                f"Abstaining on query '{request.query}': top score {top_score:.3f} "
                f"is below threshold {self.score_threshold:.3f}"
            )
            EIG_RAG_QUERIES.labels(outcome="insufficient_evidence").inc()
            return RAGQueryResponse(
                query=request.query,
                answer=INSUFFICIENT_EVIDENCE_MESSAGE,
                insufficient_evidence=True,
                chunks_evaluated=len(reranked_candidates),
                execution_time_seconds=time.time() - start_time
            )

        # 6. Context Window Budgeting & Deduplication
        budgeted_chunks = self.context_budgeter.select_budgeted_chunks(reranked_candidates)

        # 7. Grounded Answer Synthesis with Citations
        answer, citations = self._build_grounded_answer(request.query, budgeted_chunks)

        elapsed = time.time() - start_time
        EIG_RAG_QUERIES.labels(outcome="grounded").inc()

        return RAGQueryResponse(
            query=request.query,
            answer=answer,
            citations=citations,
            insufficient_evidence=False,
            chunks_evaluated=len(budgeted_chunks),
            execution_time_seconds=elapsed
        )
