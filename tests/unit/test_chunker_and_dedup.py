"""Unit tests for semantic chunking and duplicate detection."""

import pytest
from eig.ingestion.models import DocumentMetadata, ExtractedSection
from eig.ingestion.chunker import DocumentChunker
from eig.ingestion.deduplication import compute_content_hash, generate_document_id, check_duplicate_document
from eig.core.database import DocumentRegistryModel


def test_chunker_overlap_and_provenance():
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
    sections = [
        ExtractedSection(
            text="First sentence of section one. Second sentence of section one. Third sentence is quite long.",
            page_number=1,
            section_header="Introduction"
        ),
        ExtractedSection(
            text="First sentence of page two. Second sentence continues the concept.",
            page_number=2,
            section_header="Methodology"
        )
    ]
    meta = DocumentMetadata(
        tenant_id="tenant_x",
        document_id="doc_123",
        source_filename="test.pdf",
        department="engineering",
        access_tier=1,
        content_hash="abc456"
    )

    chunks = chunker.chunk_sections(sections, meta)
    assert len(chunks) >= 2
    # Check that provenance is preserved across chunks
    assert chunks[0].page_number == 1
    assert chunks[-1].page_number == 2
    assert chunks[0].chunk_id == "doc_123_0"


@pytest.mark.asyncio
async def test_deduplication_and_hashing(test_db_session):
    payload = b"Sample enterprise contract payload for hashing"
    content_hash = compute_content_hash(payload)
    doc_id = generate_document_id("tenant_alpha", content_hash)

    # Initial check: not duplicate
    is_dup, existing = await check_duplicate_document(test_db_session, "tenant_alpha", content_hash)
    assert is_dup is False
    assert existing is None

    # Insert record
    rec = DocumentRegistryModel(
        id=doc_id,
        tenant_id="tenant_alpha",
        source_filename="contract.pdf",
        department="legal",
        access_tier=1,
        content_hash=content_hash,
        status="INDEXED"
    )
    test_db_session.add(rec)
    await test_db_session.commit()

    # Subsequent check: duplicate detected
    is_dup2, existing2 = await check_duplicate_document(test_db_session, "tenant_alpha", content_hash)
    assert is_dup2 is True
    assert existing2.id == doc_id

    # Check cross-tenant isolation: same hash in tenant_beta is not duplicate for tenant_beta
    is_dup_beta, _ = await check_duplicate_document(test_db_session, "tenant_beta", content_hash)
    assert is_dup_beta is False
