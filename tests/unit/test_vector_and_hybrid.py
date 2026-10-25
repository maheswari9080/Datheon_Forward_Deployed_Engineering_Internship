"""Unit tests for vector indexing, metadata filters, and hybrid search."""

from eig.ingestion.models import DocumentChunk
from eig.ingestion.vector_store.qdrant_store import QdrantVectorStore
from eig.rag.hybrid_retriever import HybridRetriever


def test_chroma_metadata_filtering(test_chroma_store, mock_embedding_provider, user_tenant_a_eng):
    # Create two chunks: one authorized for engineering tier 2, one finance tier 3
    emb1 = mock_embedding_provider.embed_query("Firewall and network infrastructure security")
    c1 = DocumentChunk(
        chunk_id="c_eng_1",
        document_id="doc_eng",
        tenant_id="tenant_a",
        text="Firewall and network infrastructure security guidelines",
        department="engineering",
        access_tier=2,
        source_filename="eng.md",
        content_hash="h1",
        chunk_index=0,
        embedding=emb1
    )

    emb2 = mock_embedding_provider.embed_query("Q3 Financial audit and executive compensation")
    c2 = DocumentChunk(
        chunk_id="c_fin_1",
        document_id="doc_fin",
        tenant_id="tenant_a",
        text="Q3 Financial audit and executive compensation records",
        department="finance",
        access_tier=3,
        source_filename="fin.md",
        content_hash="h2",
        chunk_index=0,
        embedding=emb2
    )

    test_chroma_store.index_chunks([c1, c2])

    retriever = HybridRetriever(
        vector_store=test_chroma_store,
        embedding_provider=mock_embedding_provider
    )

    # Search as Alice (Engineering, tier 2)
    results = retriever.search_hybrid(
        query="security firewall",
        user=user_tenant_a_eng,
        top_k=5
    )

    assert len(results) > 0
    # Must only return engineering chunk; finance chunk must be strictly filtered
    chunk_ids = [chunk.chunk_id for chunk, _ in results]
    assert "c_eng_1" in chunk_ids
    assert "c_fin_1" not in chunk_ids


def test_qdrant_adapter_in_memory(mock_embedding_provider):
    store = QdrantVectorStore(in_memory=True, vector_size=64)
    emb = mock_embedding_provider.embed_query("Distributed compute cluster")
    chunk = DocumentChunk(
        chunk_id="qd_1",
        document_id="qd_doc",
        tenant_id="tenant_x",
        text="Distributed compute cluster architecture",
        department="operations",
        access_tier=1,
        source_filename="qd.txt",
        content_hash="qdh",
        chunk_index=0,
        embedding=emb
    )
    indexed = store.index_chunks([chunk])
    assert indexed == 1

    search_res = store.search_similarity(
        query_vector=emb,
        top_k=2,
        filter_criteria={"$and": [{"tenant_id": {"$eq": "tenant_x"}}]}
    )
    assert len(search_res) == 1
    assert search_res[0][0].chunk_id == "qd_1"
