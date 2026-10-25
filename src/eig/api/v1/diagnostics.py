"""Diagnostics and audit integrity endpoints (secrets strictly protected)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from eig.core.database import get_db
from eig.core.security import UserIdentity, get_current_user
from eig.agent.audit_store import AuditStore
from eig.config import settings

diagnostics_router = APIRouter(prefix="/diagnostics", tags=["Diagnostics & Integrity"])
audit_store = AuditStore()


@diagnostics_router.get("/config", summary="Safe Configuration Diagnostics")
async def get_config_diagnostics(user: UserIdentity = Depends(get_current_user)):
    """
    Return operational configuration diagnostics without secret disclosure.
    Security Invariant #10: Secrets and keys are strictly redacted.
    """
    return settings.safe_diagnostics()


@diagnostics_router.get("/audit-integrity", summary="Audit Log Chain Verification")
async def verify_audit_integrity(
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Verify cryptographic hash chain integrity of tenant's audit trail."""
    is_valid, msg = await audit_store.verify_chain_integrity(session=db, tenant_id=user.tenant_id)
    return {
        "tenant_id": user.tenant_id,
        "chain_intact": is_valid,
        "verification_message": msg
    }
