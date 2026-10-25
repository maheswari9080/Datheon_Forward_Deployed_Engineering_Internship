"""Abstract interface for text embedding providers."""

from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract contract for generating normalized dense vector embeddings."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of produced vectors."""
        pass

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a batch of text documents."""
        pass

    def embed_query(self, query: str) -> List[float]:
        """Compute embedding for a single user query."""
        results = self.embed_texts([query])
        return results[0]
