"""Cross-encoder reranking abstraction with local model and fallback support."""

import time
from abc import ABC, abstractmethod
from typing import List, Tuple
from eig.core.logging import logger
from eig.core.metrics import EIG_RERANK_LATENCY
from eig.ingestion.models import DocumentChunk


class BaseReranker(ABC):
    """Abstract contract for scoring (query, chunk) candidate pairs."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: List[Tuple[DocumentChunk, float]],
        top_n: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        pass


class CrossEncoderReranker(BaseReranker):
    """Local cross-encoder reranker with graceful deterministic fallback."""

    def __init__(self, model_name: str = "bge-reranker-base"):
        self.model_name = model_name
        self._model = None

        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(model_name)
            logger.info(f"Initialized local CrossEncoder model: {model_name}")
        except Exception:
            logger.info(f"CrossEncoder model '{model_name}' offline. Using exact token-affinity reranker.")

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[DocumentChunk, float]],
        top_n: int = 5
    ) -> List[Tuple[DocumentChunk, float]]:
        if not candidates:
            return []

        start_time = time.time()
        scored_pairs: List[Tuple[DocumentChunk, float]] = []

        if self._model is not None:
            try:
                pairs = [[query, chunk.text] for chunk, _ in candidates]
                scores = self._model.predict(pairs)
                for (chunk, _), score in zip(candidates, scores):
                    # Sigmoid normalizer if scores are unbounded logits
                    norm_score = 1.0 / (1.0 + (2.71828 ** (-float(score))))
                    scored_pairs.append((chunk, norm_score))
            except Exception as exc:
                logger.warning(f"Cross-encoder prediction failed: {exc}. Using base scores.")
                scored_pairs = list(candidates)
        else:
            # Deterministic affinity reranker: combines initial score with exact query token coverage
            query_words = set(query.lower().split())
            for chunk, initial_score in candidates:
                chunk_words = set(chunk.text.lower().split())
                overlap = len(query_words.intersection(chunk_words))
                coverage = overlap / max(1, len(query_words))
                combined_score = (initial_score * 0.4) + (coverage * 0.6)
                scored_pairs.append((chunk, combined_score))

        # Sort descending by reranked score
        reranked = sorted(scored_pairs, key=lambda x: x[1], reverse=True)
        elapsed = time.time() - start_time
        EIG_RERANK_LATENCY.labels(status="success").observe(elapsed)

        return reranked[:top_n]
