"""ChromaDB vector store implementation with metadata filtering and cosine distance."""

import os
from typing import List, Dict, Any, Tuple, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from eig.core.logging import logger
from eig.ingestion.models import DocumentChunk
from eig.ingestion.vector_store.base import BaseVectorStore


class ChromaVectorStore(BaseVectorStore):
    """Local ChromaDB store enforcing cosine similarity and multi-tenant metadata filters."""

    def __init__(self, persist_directory: str = "./data/chroma_db", collection_name: str = "eig_enterprise_knowledge"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Initialized ChromaVectorStore at '{persist_directory}' collection '{collection_name}'")

    def index_chunks(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        embeddings = [c.embedding for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.to_metadata_dict() for c in chunks]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        return len(chunks)

    def search_similarity(
        self,
        query_vector: List[float],
        top_k: int,
        filter_criteria: Dict[str, Any]
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Query ChromaDB with vector and pre-retrieval where filter.
        In Chroma with cosine distance: distance is 1 - cosine_similarity.
        Similarity score = max(0.0, 1.0 - distance).
        """
        count = self.collection.count()
        if count == 0:
            return []

        effective_k = min(top_k, count)
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=effective_k,
            where=filter_criteria if filter_criteria else None,
            include=["documents", "metadatas", "distances"]
        )

        output: List[Tuple[DocumentChunk, float]] = []
        if not results or not results["ids"] or not results["ids"][0]:
            return output

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for chunk_id, doc_text, meta, dist in zip(ids, documents, metadatas, distances):
            # Compute cosine similarity from cosine distance
            score = max(0.0, 1.0 - float(dist))

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=meta["document_id"],
                tenant_id=meta["tenant_id"],
                text=doc_text,
                page_number=meta.get("page_number") if meta.get("page_number") != -1 else None,
                row_number=meta.get("row_number") if meta.get("row_number") != -1 else None,
                section_header=meta.get("section_header") or None,
                department=meta["department"],
                access_tier=meta["access_tier"],
                document_date=meta.get("document_date") if meta.get("document_date") != "UNAVAILABLE" else None,
                source_filename=meta["source_filename"],
                content_hash=meta["content_hash"],
                chunk_index=meta["chunk_index"],
            )
            output.append((chunk, score))

        return output

    def delete_document(self, tenant_id: str, document_id: str) -> int:
        """Purge document chunks matching tenant_id and document_id."""
        filter_dict = {
            "$and": [
                {"tenant_id": {"$eq": tenant_id}},
                {"document_id": {"$eq": document_id}}
            ]
        }
        # Query matching IDs first to return deleted count
        results = self.collection.get(where=filter_dict, include=[])
        matching_ids = results["ids"] if results and "ids" in results else []
        if matching_ids:
            self.collection.delete(ids=matching_ids)
        return len(matching_ids)

    def count(self, tenant_id: Optional[str] = None) -> int:
        if tenant_id:
            res = self.collection.get(where={"tenant_id": {"$eq": tenant_id}}, include=[])
            return len(res["ids"]) if res and "ids" in res else 0
        return self.collection.count()
