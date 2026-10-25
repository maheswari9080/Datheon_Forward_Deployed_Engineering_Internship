"""Local SentenceTransformers embedding provider with automatic mock fallback."""

from typing import List, Optional
from eig.core.logging import logger
from eig.ingestion.embeddings.base import BaseEmbeddingProvider
from eig.ingestion.embeddings.mock_provider import DeterministicMockEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Integrates sentence-transformers models locally when available."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self._model_name = model_name
        self._dimension = dimension
        self._model = None
        self._fallback_provider: Optional[DeterministicMockEmbeddingProvider] = None

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            logger.info(f"Initialized local SentenceTransformer model: {model_name}")
        except Exception as exc:
            logger.warning(
                f"SentenceTransformer not available ({str(exc)}). "
                "Engaging DeterministicMockEmbeddingProvider for local-first operations."
            )
            self._fallback_provider = DeterministicMockEmbeddingProvider(dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if self._model is not None:
            raw_embeddings = self._model.encode(texts, normalize_embeddings=True)
            return [emb.tolist() for emb in raw_embeddings]
        elif self._fallback_provider is not None:
            return self._fallback_provider.embed_texts(texts)
        else:
            raise RuntimeError("No embedding provider initialized")
