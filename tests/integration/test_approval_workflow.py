"""Integration tests for HMAC approval engine, replay defense, expiration, and audit chain."""

import datetime
import pytest
from fastapi import HTTPException
from eig.core.security import UserIdentity
from eig.agent.approval_engine import ApprovalEngine
from eig.agent.audit_store import AuditStore
from eig.agent.orchestrator import AgentOrchestrator
from eig.agent.schemas import AgentTaskRequest


@pytest.fixture
def enterprise_sales_lead():
    return UserIdentity(
        user_id="usr_lead_vp",
        tenant_id="tenant_aerospace",
        username="vp_sales",
        roles=["sales", "admin"],
        departments=["sales"],
        clearance_level=3
    )


@pytest.mark.asyncio
async def test_full_approval_lifecycle(test_db_session, enterprise_sales_lead):
    """
    Test Complete Flow:
    1. Write operation triggers APPROVAL_REQUIRED with cryptographic token.
    2. Approval record is verified and executed.
    3. Replay attack attempt is strictly rejected with 409 Conflict.
    4. Audit trail cryptographic chain is intact.
    """
    orchestrator = AgentOrchestrator()

    # 1. Request sensitive write operation
    req = AgentTaskRequest(
        prompt="Update lead LEAD-4891 to WON",
        tool_name="update_lead_status",
        tool_arguments={
            "lead_id": "LEAD-4891",
            "new_status": "WON",
            "reason": "Signed contract received from legal"
        }
    )

    resp = await orchestrator.execute_task(test_db_session, req, enterprise_sales_lead)
    assert resp.outcome == "APPROVAL_REQUIRED"
    assert resp.approval_request_id is not None
    appr_id = resp.approval_request_id

    # 2. Approve and Execute
    approval_resp = await orchestrator.execute_approved_operation(
        session=test_db_session,
        approval_id=appr_id,
        acting_user=enterprise_sales_lead
    )
    assert approval_resp.outcome == "COMPLETED"
    assert approval_resp.result["success"] is True
    assert approval_resp.result["new_status"] == "WON"

    # 3. Replay Attack Prevention: Attempting to resolve the same approval twice MUST fail
    with pytest.raises(HTTPException) as exc_info:
        await orchestrator.execute_approved_operation(
            session=test_db_session,
            approval_id=appr_id,
            acting_user=enterprise_sales_lead
        )
    assert exc_info.value.status_code == 409

    # 4. Audit Chain Verification
    audit_store = AuditStore()
    valid, msg = await audit_store.verify_chain_integrity(test_db_session, enterprise_sales_lead.tenant_id)
    assert valid is True
    assert "Integrity verified" in msg


@pytest.mark.asyncio
async def test_approval_token_expiration(test_db_session, enterprise_sales_lead):
    """Verify that expired approval tokens fail closed and cannot be executed."""
    # Initialize engine with 0-second TTL
    short_ttl_engine = ApprovalEngine(ttl_seconds=-10)

    appr_id, token, exp = await short_ttl_engine.create_approval_request(
        session=test_db_session,
        user=enterprise_sales_lead,
        tool_name="update_lead_status",
        validated_args={"lead_id": "LEAD-4891", "new_status": "LOST", "reason": "Expired lead"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await short_ttl_engine.resolve_approval(
            session=test_db_session,
            approval_id=appr_id,
            approve=True,
            acting_user=enterprise_sales_lead
        )
    assert exc_info.value.status_code == 410
