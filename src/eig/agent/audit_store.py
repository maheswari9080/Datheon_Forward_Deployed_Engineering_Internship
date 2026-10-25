"""Append-only, cryptographically linked audit event store with integrity verification."""

import datetime
import hashlib
import json
from typing import Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eig.core.database import AuditEventModel
from eig.core.logging import logger


class AuditStore:
    """Manages append-only audit events with cryptographic chain linking."""

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    async def record_audit_event(
        self,
        session: AsyncSession,
        tenant_id: str,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any]
    ) -> AuditEventModel:
        """Append an immutable audit record cryptographically linked to the previous tenant event."""
        # Retrieve previous event in tenant
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.tenant_id == tenant_id)
            .order_by(AuditEventModel.id.desc())
            .limit(1)
        )
        res = await session.execute(stmt)
        prev_event = res.scalar_one_or_none()
        prev_hash = prev_event.current_hash if prev_event else ("0" * 64)

        now = datetime.datetime.now(datetime.timezone.utc)
        details_json = self._canonical_json(details)

        # Calculate cryptographic link hash
        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode("utf-8"))
        hasher.update(tenant_id.encode("utf-8"))
        hasher.update(user_id.encode("utf-8"))
        hasher.update(action.encode("utf-8"))
        hasher.update(resource.encode("utf-8"))
        hasher.update(details_json.encode("utf-8"))
        hasher.update(now.isoformat().encode("utf-8"))
        current_hash = hasher.hexdigest()

        event = AuditEventModel(
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            resource=resource,
            details_json=details_json,
            timestamp=now,
            prev_hash=prev_hash,
            current_hash=current_hash
        )
        session.add(event)
        await session.commit()
        logger.info(f"Recorded audit event #{event.id} ({action}) for tenant {tenant_id}")
        return event

    async def verify_chain_integrity(
        self,
        session: AsyncSession,
        tenant_id: str
    ) -> Tuple[bool, str]:
        """Verify the cryptographic chain consistency of all audit records for a tenant."""
        stmt = (
            select(AuditEventModel)
            .where(AuditEventModel.tenant_id == tenant_id)
            .order_by(AuditEventModel.id.asc())
        )
        res = await session.execute(stmt)
        events = res.scalars().all()

        expected_prev_hash = "0" * 64
        for idx, event in enumerate(events):
            if event.prev_hash != expected_prev_hash:
                return False, f"Broken chain link at audit event #{event.id}: prev_hash mismatch"

            hasher = hashlib.sha256()
            hasher.update(expected_prev_hash.encode("utf-8"))
            hasher.update(event.tenant_id.encode("utf-8"))
            hasher.update(event.user_id.encode("utf-8"))
            hasher.update(event.action.encode("utf-8"))
            hasher.update(event.resource.encode("utf-8"))
            hasher.update(event.details_json.encode("utf-8"))
            # Make sure event.timestamp is ISO formatted
            ts = event.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=datetime.timezone.utc)
            hasher.update(ts.isoformat().encode("utf-8"))
            computed_hash = hasher.hexdigest()

            if computed_hash != event.current_hash:
                return False, f"Tampered record payload detected at audit event #{event.id}"

            expected_prev_hash = event.current_hash

        return True, f"Integrity verified for {len(events)} audit events."
