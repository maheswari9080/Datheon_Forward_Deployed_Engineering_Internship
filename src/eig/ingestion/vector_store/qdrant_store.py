"""Qdrant client adapter for enterprise vector operations."""

from typing import List, Dict, Any, Tuple, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from eig.core.logging import logger
from eig.ingestion.models import DocumentChunk
from eig.ingestion.vector_store.base import BaseVectorStore


class QdrantVectorStore(BaseVectorStore):
    """Qdrant adapter supporting in-memory or clustered vector retrieval."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "eig_enterprise_knowledge",
        vector_size: int = 384,
        in_memory: bool = False
    ):
        self.collection_name = collection_name
        self.vector_size = vector_size

        if in_memory:
            self.client = QdrantClient(location=":memory:")
            logger.info("Initialized QdrantVectorStore in-memory")
        else:
            try:
                self.client = QdrantClient(host=host, port=port, timeout=3.0)
                # Test connection
                self.client.get_collections()
                logger.info(f"Connected to remote Qdrant at {host}:{port}")
            except Exception as exc:
                logger.warning(f"Could not connect to Qdrant at {host}:{port} ({str(exc)}). Falling back to in-memory mode.")
                self.client = QdrantClient(location=":memory:")

        # Ensure collection exists
        collections = self.client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0

        import uuid
        points = []
        for c in chunks:
            point_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, c.chunk_id))
            points.append(
                qmodels.PointStruct(
                    id=point_uuid,
                    vector=c.embedding,
                    payload={
                        **c.to_metadata_dict(),
                        "text": c.text,
                        "original_chunk_id": c.chunk_id
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        return len(chunks)

    def search_similarity(
        self,
        query_vector: List[float],
        top_k: int,
        filter_criteria: Dict[str, Any]
    ) -> List[Tuple[DocumentChunk, float]]:
        # Map simple filter dictionary to Qdrant filter
        q_filter = None
        must_conditions = []

        if filter_criteria and "$and" in filter_criteria:
            for clause in filter_criteria["$and"]:
                for key, op_dict in clause.items():
                    if "$eq" in op_dict:
                        must_conditions.append(
                            qmodels.FieldCondition(
                                key=key,
                                match=qmodels.MatchValue(value=op_dict["$eq"])
                            )
                        )
                    elif "$in" in op_dict:
                        must_conditions.append(
                            qmodels.FieldCondition(
                                key=key,
                                match=qmodels.MatchAny(any=op_dict["$in"])
                            )
                        )
                    elif "$lte" in op_dict:
                        must_conditions.append(
                            qmodels.FieldCondition(
                                key=key,
                                range=qmodels.Range(lte=op_dict["$lte"])
                            )
                        )

        if must_conditions:
            q_filter = qmodels.Filter(must=must_conditions)

        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vector,
                limit=top_k,
                query_filter=q_filter
            )
            hits = response.points
        else:
            hits = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=q_filter
            )

        output: List[Tuple[DocumentChunk, float]] = []
        for hit in hits:
            payload = hit.payload or {}
            chunk = DocumentChunk(
                chunk_id=str(payload.get("original_chunk_id", hit.id)),
                document_id=payload.get("document_id", ""),
                tenant_id=payload.get("tenant_id", ""),
                text=payload.get("text", ""),
                page_number=payload.get("page_number") if payload.get("page_number") != -1 else None,
                row_number=payload.get("row_number") if payload.get("row_number") != -1 else None,
                section_header=payload.get("section_header") or None,
                department=payload.get("department", ""),
                access_tier=payload.get("access_tier", 1),
                document_date=payload.get("document_date") if payload.get("document_date") != "UNAVAILABLE" else None,
                source_filename=payload.get("source_filename", ""),
                content_hash=payload.get("content_hash", ""),
                chunk_index=payload.get("chunk_index", 0),
            )
            output.append((chunk, float(hit.score)))

        return output

    def delete_document(self, tenant_id: str, document_id: str) -> int:
        filter_spec = qmodels.Filter(
            must=[
                qmodels.FieldCondition(key="tenant_id", match=qmodels.MatchValue(value=tenant_id)),
                qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=document_id)),
            ]
        )
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=filter_spec
        )
        return 1

    def count(self, tenant_id: Optional[str] = None) -> int:
        info = self.client.get_collection(self.collection_name)
        return info.points_count or 0
