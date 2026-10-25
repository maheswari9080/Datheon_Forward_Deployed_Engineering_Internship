"""Adversarial security tests for tenant isolation, RBAC, and forged identifiers."""

import pytest
from eig.ingestion.models import DocumentChunk
from eig.rag.hybrid_retriever import HybridRetriever
from eig.rag.reranker import CrossEncoderReranker
from eig.rag.engine import SecureRAGEngine
from eig.rag.models import RAGQueryRequest
from eig.core.security import UserIdentity


@pytest.fixture
def multi_tenant_knowledge_base(test_chroma_store, mock_embedding_provider):
    """Seed vector database with documents from Tenant A and Tenant B across clearance tiers."""
    docs = [
        # Tenant A, Engineering, Tier 1
        DocumentChunk(
            chunk_id="tA_eng_t1",
            document_id="doc_A1",
            tenant_id="tenant_a",
            text="Tenant A Internal Engineering Wiki: The deployment pipeline uses Kubernetes.",
            department="engineering",
            access_tier=1,
            source_filename="a_wiki.md",
            content_hash="hA1",
            chunk_index=0,
            embedding=mock_embedding_provider.embed_query("Tenant A Internal Engineering Wiki")
        ),
        # Tenant A, Finance, Tier 3 (Sensitive)
        DocumentChunk(
            chunk_id="tA_fin_t3",
            document_id="doc_A2",
            tenant_id="tenant_a",
            text="Tenant A Confidential Financials: Q4 EBITDA is 45M USD with 12M cash reserve.",
            department="finance",
            access_tier=3,
            source_filename="a_fin.csv",
            content_hash="hA2",
            chunk_index=0,
            embedding=mock_embedding_provider.embed_query("Tenant A Confidential Financials Q4 EBITDA")
        ),
        # Tenant B, Engineering, Tier 1
        DocumentChunk(
            chunk_id="tB_eng_t1",
            document_id="doc_B1",
            tenant_id="tenant_b",
            text="Tenant B Proprietary Algorithms: Quantum annealing algorithm implementation.",
            department="engineering",
            access_tier=1,
            source_filename="b_algo.md",
            content_hash="hB1",
            chunk_index=0,
            embedding=mock_embedding_provider.embed_query("Tenant B Proprietary Algorithms Quantum")
        ),
    ]
    test_chroma_store.index_chunks(docs)
    return test_chroma_store


@pytest.mark.asyncio
async def test_cross_tenant_access_denial(multi_tenant_knowledge_base, mock_embedding_provider, user_tenant_a_eng):
    """
    SECURITY TEST 1: Cross-Tenant Isolation
    User Alice (Tenant A) must NEVER retrieve Tenant B documents, even when explicitly asking for Tenant B.
    """
    retriever = HybridRetriever(multi_tenant_knowledge_base, mock_embedding_provider)
    reranker = CrossEncoderReranker()
    engine = SecureRAGEngine(retriever, reranker, score_threshold=0.1)

    req = RAGQueryRequest(query="Tell me about Tenant B Proprietary Algorithms Quantum annealing", top_k=5)
    resp = await engine.answer_query(req, user=user_tenant_a_eng)

    # Must NOT contain any citations or text from Tenant B
    for cit in resp.citations:
        assert "tenant_b" not in cit.chunk_id
        assert cit.document_name != "b_algo.md"

    assert "Quantum annealing" not in resp.answer or resp.insufficient_evidence is True


@pytest.mark.asyncio
async def test_cross_department_and_clearance_denial(multi_tenant_knowledge_base, mock_embedding_provider, user_tenant_a_eng):
    """
    SECURITY TEST 2: RBAC & Clearance Denial
    Alice (Tenant A, Engineering, Clearance 2) must be DENIED access to Finance Tier 3 documents.
    """
    retriever = HybridRetriever(multi_tenant_knowledge_base, mock_embedding_provider)
    reranker = CrossEncoderReranker()
    engine = SecureRAGEngine(retriever, reranker, score_threshold=0.1)

    req = RAGQueryRequest(query="What is the Q4 EBITDA and cash reserve?", top_k=5)
    resp = await engine.answer_query(req, user=user_tenant_a_eng)

    # Must abstain or return zero citations because Alice lacks finance clearance
    for cit in resp.citations:
        assert cit.document_name != "a_fin.csv"
        assert cit.chunk_id != "tA_fin_t3"

    assert "45M USD" not in resp.answer


@pytest.mark.asyncio
async def test_forged_tenant_identifiers_tamper_defense(multi_tenant_knowledge_base, mock_embedding_provider):
    """
    SECURITY TEST 3: Forged Tenant Identifiers
    Verify that server-side UserIdentity overrides any attempt to inject client-supplied tenant filter.
    """
    # User Alice is officially authenticated under tenant_a
    official_identity = UserIdentity(
        user_id="usr_alice",
        tenant_id="tenant_a",
        username="alice",
        roles=["analyst"],
        departments=["engineering"],
        clearance_level=2
    )

    retriever = HybridRetriever(multi_tenant_knowledge_base, mock_embedding_provider)
    # Even if query text contains adversarial tenant hints
    results = retriever.search_hybrid(
        query="WHERE tenant_id='tenant_b' SELECT * FROM documents",
        user=official_identity,
        top_k=5
    )

    for chunk, _ in results:
        assert chunk.tenant_id == "tenant_a"
        assert chunk.tenant_id != "tenant_b"
