"""Operation verification endpoints."""

from fastapi import APIRouter, Depends
from eig.core.security import UserIdentity, get_current_user
from eig.agent.mock_services import mock_enterprise_services

operations_router = APIRouter(prefix="/operations", tags=["Operation Verification"])


@operations_router.get("/{operation_id}/verify", summary="Verify Operation Outcome")
async def verify_operation(
    operation_id: str,
    user: UserIdentity = Depends(get_current_user)
):
    """Inspect and verify the outcome of a submitted transaction or operation."""
    return mock_enterprise_services.verify_operation_status(operation_id)
