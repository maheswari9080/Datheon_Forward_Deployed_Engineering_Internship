"""End-to-end ingestion ETL pipeline managing parsing, chunking, embedding, and indexing."""

import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from eig.config import settings
from eig.core.database import DocumentRegistryModel
from eig.core.logging import logger
from eig.core.metrics import EIG_INGESTION_DOCS, EIG_INGESTION_CHUNKS, EIG_INGESTION_DURATION
from eig.ingestion.models import (
    DocumentMetadata,
    DocumentChunk,
    IngestionReport,
    IngestionItemError,
)
from eig.ingestion.deduplication import compute_content_hash, generate_document_id, check_duplicate_document
from eig.ingestion.chunker import DocumentChunker
from eig.ingestion.parsers.pdf_parser import PDFDocumentParser
from eig.ingestion.parsers.csv_parser import CSVDocumentParser
from eig.ingestion.parsers.markdown_parser import MarkdownDocumentParser
from eig.ingestion.embeddings.base import BaseEmbeddingProvider
from eig.ingestion.vector_store.base import BaseVectorStore


class IngestionPipeline:
    """Orchestrates parsing, deduplication, chunking, embedding, and vector indexing."""

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedding_provider: BaseEmbeddingProvider,
        chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = settings.DEFAULT_CHUNK_OVERLAP
    ):
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.pdf_parser = PDFDocumentParser()
        self.csv_parser = CSVDocumentParser()
        self.md_parser = MarkdownDocumentParser()

    def _get_parser_for_filename(self, filename: str):
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return self.pdf_parser, "pdf"
        elif lower.endswith(".csv"):
            return self.csv_parser, "csv"
        elif lower.endswith((".md", ".markdown", ".txt")):
            return self.md_parser, "markdown"
        else:
            raise ValueError(f"Unsupported file format: {filename}. Supported formats: PDF, CSV, Markdown.")

    async def ingest_single_document(
        self,
        session: AsyncSession,
        content_bytes: bytes,
        filename: str,
        tenant_id: str,
        department: str,
        access_tier: int = 1,
        document_date: Optional[str] = None,
        force_reindex: bool = False
    ) -> Tuple[str, int, bool]:
        """
        Ingest a single document into the platform.
        Returns: (document_id, chunk_count, is_duplicate)
        """
        start_time = time.time()
        file_size = len(content_bytes)

        if file_size > settings.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File {filename} ({file_size} bytes) exceeds limit of {settings.MAX_FILE_SIZE_BYTES} bytes."
            )

        # 1. Deduplication check
        content_hash = compute_content_hash(content_bytes)
        document_id = generate_document_id(tenant_id, content_hash)

        is_duplicate, existing_doc = await check_duplicate_document(session, tenant_id, content_hash)
        if is_duplicate and not force_reindex and existing_doc:
            logger.info(f"Duplicate document detected for tenant '{tenant_id}': {filename} (ID: {existing_doc.id})")
            return existing_doc.id, existing_doc.total_chunks, True

        # 2. Select parser & parse
        parser, file_type = self._get_parser_for_filename(filename)
        with EIG_INGESTION_DURATION.labels(stage="parse").time():
            sections = parser.parse(content_bytes, filename)

        # 3. Create document metadata
        metadata = DocumentMetadata(
            tenant_id=tenant_id,
            document_id=document_id,
            source_filename=filename,
            department=department,
            access_tier=access_tier,
            document_date=document_date,
            content_hash=content_hash,
            parser_version="1.0.0"
        )

        # 4. Chunk document
        with EIG_INGESTION_DURATION.labels(stage="chunk").time():
            chunks = self.chunker.chunk_sections(sections, metadata)

        # 5. Generate embeddings
        chunk_texts = [c.text for c in chunks]
        with EIG_INGESTION_DURATION.labels(stage="embed").time():
            embeddings = self.embedding_provider.embed_texts(chunk_texts)

        for chunk, emb in zip(chunks, embeddings):
            chunk.embedding = emb

        # 6. Index into Vector Store
        with EIG_INGESTION_DURATION.labels(stage="index").time():
            if is_duplicate and force_reindex:
                # Remove prior chunks before updating
                self.vector_store.delete_document(tenant_id, document_id)
            self.vector_store.index_chunks(chunks)

        # 7. Update SQL Document Registry
        if existing_doc:
            existing_doc.source_filename = filename
            existing_doc.department = department
            existing_doc.access_tier = access_tier
            existing_doc.document_date = document_date
            existing_doc.total_chunks = len(chunks)
            existing_doc.status = "INDEXED"
        else:
            new_doc = DocumentRegistryModel(
                id=document_id,
                tenant_id=tenant_id,
                source_filename=filename,
                department=department,
                access_tier=access_tier,
                document_date=document_date,
                content_hash=content_hash,
                parser_version="1.0.0",
                total_chunks=len(chunks),
                status="INDEXED"
            )
            session.add(new_doc)

        await session.commit()

        # Update metrics
        EIG_INGESTION_DOCS.labels(file_type=file_type, status="success").inc()
        EIG_INGESTION_CHUNKS.labels(status="indexed").inc(len(chunks))
        elapsed = time.time() - start_time
        logger.info(f"Ingested {filename} (ID: {document_id}) with {len(chunks)} chunks in {elapsed:.3f}s")

        return document_id, len(chunks), False

    async def ingest_batch(
        self,
        session: AsyncSession,
        files: List[Tuple[str, bytes]],  # (filename, content_bytes)
        tenant_id: str,
        department: str,
        access_tier: int = 1,
        document_date: Optional[str] = None
    ) -> IngestionReport:
        """Batch ingestion supporting partial failures and detailed reports."""
        job_id = str(uuid.uuid4())
        start_time = time.time()

        if len(files) > settings.MAX_BATCH_DOCUMENTS:
            raise ValueError(f"Batch size {len(files)} exceeds maximum limit {settings.MAX_BATCH_DOCUMENTS}")

        indexed_docs = 0
        skipped_duplicates = 0
        failed_docs = 0
        total_chunks = 0
        errors: List[IngestionItemError] = []
        doc_ids: List[str] = []

        for filename, content in files:
            try:
                doc_id, chunk_cnt, is_dup = await self.ingest_single_document(
                    session=session,
                    content_bytes=content,
                    filename=filename,
                    tenant_id=tenant_id,
                    department=department,
                    access_tier=access_tier,
                    document_date=document_date
                )
                doc_ids.append(doc_id)
                if is_dup:
                    skipped_duplicates += 1
                else:
                    indexed_docs += 1
                    total_chunks += chunk_cnt
            except Exception as exc:
                failed_docs += 1
                error_msg = str(exc)
                logger.error(f"Failed to ingest {filename}: {error_msg}")
                _, file_type = ("unknown", "unknown")
                try:
                    _, file_type = self._get_parser_for_filename(filename)
                except Exception:
                    pass
                EIG_INGESTION_DOCS.labels(file_type=file_type, status="failure").inc()
                errors.append(
                    IngestionItemError(
                        filename=filename,
                        error_type=exc.__class__.__name__,
                        detail=error_msg
                    )
                )

        duration = time.time() - start_time
        return IngestionReport(
            job_id=job_id,
            tenant_id=tenant_id,
            total_documents=len(files),
            indexed_documents=indexed_docs,
            skipped_duplicates=skipped_duplicates,
            failed_documents=failed_docs,
            total_chunks=total_chunks,
            duration_seconds=duration,
            errors=errors,
            document_ids=doc_ids
        )

    async def delete_document(
        self,
        session: AsyncSession,
        tenant_id: str,
        document_id: str
    ) -> bool:
        """Propagate document deletion to vector store and mark DELETED in registry."""
        stmt = (
            select(DocumentRegistryModel)
            .where(
                DocumentRegistryModel.tenant_id == tenant_id,
                DocumentRegistryModel.id == document_id
            )
            .limit(1)
        )
        res = await session.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            return False

        # Remove from vector store
        self.vector_store.delete_document(tenant_id, document_id)

        # Mark in registry
        doc.status = "DELETED"
        await session.commit()
        logger.info(f"Deleted document {document_id} from tenant {tenant_id}")
        return True
