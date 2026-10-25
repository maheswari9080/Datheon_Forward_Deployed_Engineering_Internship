"""Pytest fixtures and test environment configuration."""

import io
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport
from reportlab.pdfgen import canvas

from eig.core.database import Base
from eig.core.security import UserIdentity, create_access_token
from eig.ingestion.vector_store.chroma_store import ChromaVectorStore
from eig.ingestion.embeddings.mock_provider import DeterministicMockEmbeddingProvider
from eig.ingestion.pipeline import IngestionPipeline
from eig.rag.hybrid_retriever import HybridRetriever
from eig.rag.reranker import CrossEncoderReranker
from eig.rag.engine import SecureRAGEngine
from eig.agent.orchestrator import AgentOrchestrator
from eig.agent.approval_engine import ApprovalEngine
from eig.agent.audit_store import AuditStore
from eig.main import create_application


@pytest.fixture
def mock_embedding_provider():
    return DeterministicMockEmbeddingProvider(dimension=64)


@pytest.fixture
def test_chroma_store(tmp_path):
    persist_dir = str(tmp_path / "test_chroma")
    return ChromaVectorStore(persist_directory=persist_dir, collection_name="test_collection")


@pytest_asyncio.fixture
async def test_db_session():
    """In-memory SQLite async database session for isolated testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
def sample_pdf_bytes():
    """Generate valid 2-page PDF stream in-memory."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Enterprise Security Architecture - Page 1")
    p.drawString(100, 700, "All employees must use multi-factor authentication for SSH and VPN.")
    p.showPage()
    p.drawString(100, 750, "Incident Response Protocols - Page 2")
    p.drawString(100, 700, "Tier 3 incidents require immediate notification to the CISO within 15 minutes.")
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_csv_bytes():
    """Sample enterprise CSV data."""
    csv_text = (
        "transaction_id,department,amount_usd,date,vendor,status\n"
        "TX-101,engineering,4500.00,2026-04-10,Amazon Web Services,PAID\n"
        "TX-102,marketing,1200.00,2026-04-12,HubSpot Inc,PAID\n"
        "TX-103,engineering,89000.00,2026-04-15,NVIDIA Enterprise,APPROVED\n"
    )
    return csv_text.encode("utf-8")


@pytest.fixture
def sample_markdown_bytes():
    """Sample structured Markdown documentation."""
    md_text = (
        "# Enterprise Cloud Governance Policy\n\n"
        "Date: 2026-05-01\n\n"
        "This policy defines mandatory requirements for infrastructure deployment.\n\n"
        "## Access Control Requirements\n\n"
        "All cloud instances must be provisioned inside private subnets.\n"
        "Direct public ingress is strictly prohibited without Security Team sign-off.\n\n"
        "### Clearance Tiers\n\n"
        "Tier 1: General Employees. Tier 2: DevOps Engineers. Tier 3: Security Operations.\n"
    )
    return md_text.encode("utf-8")


@pytest.fixture
def user_tenant_a_eng():
    return UserIdentity(
        user_id="usr_alice_a",
        tenant_id="tenant_a",
        username="alice",
        roles=["analyst", "engineering"],
        departments=["engineering"],
        clearance_level=2
    )


@pytest.fixture
def user_tenant_a_finance():
    return UserIdentity(
        user_id="usr_bob_a",
        tenant_id="tenant_a",
        username="bob",
        roles=["finance"],
        departments=["finance"],
        clearance_level=1
    )


@pytest.fixture
def user_tenant_b():
    return UserIdentity(
        user_id="usr_charlie_b",
        tenant_id="tenant_b",
        username="charlie",
        roles=["admin"],
        departments=["engineering", "finance", "legal"],
        clearance_level=5
    )


@pytest_asyncio.fixture
async def async_client():
    app = create_application()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
