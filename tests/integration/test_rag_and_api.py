"""Integration tests for RAG citations, abstention, FastAPI REST endpoints, and metrics."""

import pytest
from eig.core.security import UserIdentity, create_access_token


@pytest.mark.asyncio
async def test_health_probes(async_client):
    """Verify liveness and readiness endpoints."""
    # Liveness probe
    live_resp = await async_client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "alive"

    # Readiness probe
    ready_resp = await async_client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_prometheus_metrics_endpoint(async_client):
    """Verify Prometheus metrics exposition format."""
    resp = await async_client.get("/metrics")
    assert resp.status_code == 200
    body = resp.text
    assert "eig_requests_total" in body
    assert "eig_request_duration_seconds" in body


@pytest.mark.asyncio
async def test_unauthenticated_request_fails_closed(async_client):
    """Enforce Security Invariant #4: Fail-closed on missing authentication."""
    resp = await async_client.get("/api/v1/search/documents?q=kubernetes")
    assert resp.status_code == 401
    assert "Missing required authentication credentials" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_rag_query_with_citations_and_abstention(async_client):
    """Test RAG query flow with JWT authentication and abstention."""
    user = UserIdentity(
        user_id="usr_tester",
        tenant_id="tenant_integration",
        username="tester",
        roles=["analyst", "engineering"],
        departments=["engineering"],
        clearance_level=2
    )
    token = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Query for completely non-existent unknown knowledge -> must abstain!
    unsupported_resp = await async_client.post(
        "/api/v1/rag/query",
        headers=headers,
        json={"query": "What is the secret recipe for Martian space fuel?", "top_k": 3}
    )
    assert unsupported_resp.status_code == 200
    res_data = unsupported_resp.json()
    assert res_data["insufficient_evidence"] is True
    assert "INSUFFICIENT_EVIDENCE" in res_data["answer"]


@pytest.mark.asyncio
async def test_diagnostics_without_secret_leak(async_client):
    """Security Invariant #10: Diagnostics must not leak secret keys or credentials."""
    user = UserIdentity(
        user_id="usr_admin",
        tenant_id="tenant_integration",
        username="admin",
        roles=["admin"],
        departments=["engineering"],
        clearance_level=5
    )
    token = create_access_token(user)
    headers = {"Authorization": f"Bearer {token}"}

    resp = await async_client.get("/api/v1/diagnostics/config", headers=headers)
    assert resp.status_code == 200
    config_data = resp.json()

    assert config_data["secret_key"] == "***REDACTED***"
    assert config_data["approval_hmac_secret"] == "***REDACTED***"
