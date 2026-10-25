"""Human-in-the-loop approval management endpoints."""

from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from eig.core.database import get_db, ApprovalRecordModel
from eig.core.security import UserIdentity, get_current_user
from eig.api.v1.agent import agent_orchestrator
from eig.agent.schemas import AgentTaskResponse

approvals_router = APIRouter(prefix="/approvals", tags=["Human Approvals"])


@approvals_router.get("/pending", summary="List Pending Approvals")
async def list_pending_approvals(
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all pending approval requests within the user's enterprise tenant."""
    stmt = (
        select(ApprovalRecordModel)
        .where(
            ApprovalRecordModel.tenant_id == user.tenant_id,
            ApprovalRecordModel.status == "PENDING"
        )
        .order_by(ApprovalRecordModel.created_at.desc())
    )
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "approval_id": r.id,
            "tool_name": r.tool_name,
            "arguments_json": r.arguments_json,
            "created_by": r.user_id,
            "created_at": r.created_at.isoformat(),
            "expires_at": r.expires_at.isoformat(),
            "status": r.status
        }
        for r in records
    ]


@approvals_router.post("/{approval_id}/approve", response_model=AgentTaskResponse, summary="Approve and Execute Write")
async def approve_and_execute(
    approval_id: str,
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve an irreversible write action, verifying cryptographic token and executing the tool.
    """
    return await agent_orchestrator.execute_approved_operation(
        session=db,
        approval_id=approval_id,
        acting_user=user
    )


@approvals_router.post("/{approval_id}/reject", summary="Reject Operation")
async def reject_approval(
    approval_id: str,
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Reject a pending approval request."""
    record, _ = await agent_orchestrator.approval_engine.resolve_approval(
        session=db,
        approval_id=approval_id,
        approve=False,
        acting_user=user
    )
    return {"approval_id": approval_id, "status": "REJECTED", "resolved_by": user.user_id}
