"""Abstract interface for enterprise vector database providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
from eig.ingestion.models import DocumentChunk


class BaseVectorStore(ABC):
    """Abstract contract for indexing and metadata-filtered vector retrieval."""

    @abstractmethod
    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Upsert document chunks into vector index."""
        pass

    @abstractmethod
    def search_similarity(
        self,
        query_vector: List[float],
        top_k: int,
        filter_criteria: Dict[str, Any]
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Execute cosine similarity search enforcing metadata filter criteria.
        Returns pairs of (chunk, similarity_score) where score is in [0, 1].
        """
        pass

    @abstractmethod
    def delete_document(self, tenant_id: str, document_id: str) -> int:
        """Purge all chunks associated with document ID inside the tenant."""
        pass

    @abstractmethod
    def count(self, tenant_id: Optional[str] = None) -> int:
        """Return total indexed chunks."""
        pass
