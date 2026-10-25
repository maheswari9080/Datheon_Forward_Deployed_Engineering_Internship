"""Hybrid retriever combining sparse lexical BM25 and dense vector search with RRF."""

import re
import time
from typing import List, Tuple, Dict, Any
from rank_bm25 import BM25Okapi

from eig.core.logging import logger
from eig.core.metrics import EIG_RETRIEVAL_LATENCY
from eig.core.security import UserIdentity
from eig.ingestion.models import DocumentChunk
from eig.ingestion.embeddings.base import BaseEmbeddingProvider
from eig.ingestion.vector_store.base import BaseVectorStore


class HybridRetriever:
    """
    Executes pre-retrieval RBAC filtered hybrid search.
    Enforces Security Invariants:
    #1: Derive tenant identity and permissions from server-side UserIdentity only.
    #2: Apply authorization filters BEFORE retrieval.
    #6: Prevent cross-tenant retrieval under all circumstances.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_provider: BaseEmbeddingProvider,
        rrf_k: int = 60
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.rrf_k = rrf_k

    def build_rbac_filter(self, user: UserIdentity) -> Dict[str, Any]:
        """
        Construct strict metadata filter query for vector database.
        Ensures tenant boundary, department authorization, and clearance tier limits.
        """
        and_clauses: List[Dict[str, Any]] = [
            {"tenant_id": {"$eq": user.tenant_id}},
            {"access_tier": {"$lte": user.clearance_level}}
        ]

        if "admin" not in user.roles:
            if user.departments:
                and_clauses.append({"department": {"$in": user.departments}})
            else:
                # User has no assigned departments - fail closed!
                and_clauses.append({"department": {"$eq": "__NO_ACCESS__"}})

        return {"$and": and_clauses}

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r'\w+', text.lower())

    def search_hybrid(
        self,
        query: str,
        user: UserIdentity,
        top_k: int = 10,
        candidate_pool_size: int = 25
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Execute pre-retrieval filtered hybrid retrieval:
        1. Dense cosine vector retrieval via vector store.
        2. Sparse BM25 retrieval over candidate set.
        3. Reciprocal Rank Fusion (RRF) to merge candidate lists.
        """
        start_time = time.time()
        rbac_filter = self.build_rbac_filter(user)

        # 1. Dense retrieval
        query_vector = self.embedding_provider.embed_query(query)
        dense_results = self.vector_store.search_similarity(
            query_vector=query_vector,
            top_k=candidate_pool_size,
            filter_criteria=rbac_filter
        )

        if not dense_results:
            elapsed = time.time() - start_time
            EIG_RETRIEVAL_LATENCY.labels(retriever_type="hybrid").observe(elapsed)
            return []

        # Extract candidates
        candidates = [chunk for chunk, _ in dense_results]
        candidate_map = {chunk.chunk_id: chunk for chunk in candidates}

        # 2. Sparse BM25 retrieval on retrieved candidate corpus
        corpus_tokens = [self._tokenize(chunk.text) for chunk in candidates]
        query_tokens = self._tokenize(query)

        bm25 = BM25Okapi(corpus_tokens)
        bm25_scores = bm25.get_scores(query_tokens)

        # Pair candidates with BM25 score and rank them
        sparse_ranked = sorted(
            zip(candidates, bm25_scores),
            key=lambda x: x[1],
            reverse=True
        )

        # 3. Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}

        # Dense ranking contribution
        for rank, (chunk, _) in enumerate(dense_results):
            cid = chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Sparse ranking contribution
        for rank, (chunk, _) in enumerate(sparse_ranked):
            cid = chunk.chunk_id
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (self.rrf_k + rank + 1))

        # Sort by final fused RRF score
        fused_results = sorted(
            [(candidate_map[cid], score) for cid, score in rrf_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        elapsed = time.time() - start_time
        EIG_RETRIEVAL_LATENCY.labels(retriever_type="hybrid").observe(elapsed)
        logger.debug(f"Hybrid retrieval returned {len(fused_results)} results for tenant {user.tenant_id}")

        return fused_results[:top_k]
