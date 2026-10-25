"""HMAC-signed approval engine with replay defense and expiration enforcement."""

import datetime
import hashlib
import hmac
import json
import uuid
from typing import Dict, Any, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from eig.config import settings
from eig.core.database import ApprovalRecordModel
from eig.core.logging import logger
from eig.core.metrics import EIG_APPROVAL_REQUESTS
from eig.core.security import UserIdentity


class ApprovalEngine:
    """
    Manages human-in-the-loop authorization for sensitive operations.
    Cryptographically binds approval tokens to tenant, user, tool, and validated arguments.
    Enforces replay prevention and TTL expiration.
    """

    def __init__(
        self,
        hmac_secret: str = settings.APPROVAL_HMAC_SECRET,
        ttl_seconds: int = settings.APPROVAL_TTL_SECONDS
    ):
        self.hmac_secret = hmac_secret.encode("utf-8")
        self.ttl_seconds = ttl_seconds

    def _canonical_json(self, data: Dict[str, Any]) -> str:
        """Produce deterministic canonical JSON representation."""
        return json.dumps(data, sort_keys=True, separators=(',', ':'))

    def compute_hmac_token(
        self,
        tenant_id: str,
        user_id: str,
        tool_name: str,
        arguments_json: str,
        nonce: str,
        expires_at: datetime.datetime
    ) -> str:
        """Compute HMAC-SHA256 signature binding all critical authorization dimensions."""
        args_hash = hashlib.sha256(arguments_json.encode("utf-8")).hexdigest()
        exp_epoch = int(expires_at.timestamp())
        message = f"{tenant_id}:{user_id}:{tool_name}:{args_hash}:{nonce}:{exp_epoch}".encode("utf-8")
        return hmac.new(self.hmac_secret, message, hashlib.sha256).hexdigest()

    async def create_approval_request(
        self,
        session: AsyncSession,
        user: UserIdentity,
        tool_name: str,
        validated_args: Dict[str, Any]
    ) -> Tuple[str, str, datetime.datetime]:
        """
        Create a new pending approval record.
        Returns: (approval_id, hmac_token, expires_at)
        """
        approval_id = f"appr_{uuid.uuid4().hex[:12]}"
        nonce = uuid.uuid4().hex
        now = datetime.datetime.now(datetime.timezone.utc)
        expires_at = now + datetime.timedelta(seconds=self.ttl_seconds)

        args_json = self._canonical_json(validated_args)
        token = self.compute_hmac_token(
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            tool_name=tool_name,
            arguments_json=args_json,
            nonce=nonce,
            expires_at=expires_at
        )

        record = ApprovalRecordModel(
            id=approval_id,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            tool_name=tool_name,
            arguments_json=args_json,
            hmac_token=token,
            nonce=nonce,
            status="PENDING",
            created_at=now,
            expires_at=expires_at
        )
        session.add(record)
        await session.commit()

        EIG_APPROVAL_REQUESTS.labels(tool_name=tool_name, status="created").inc()
        logger.info(f"Generated approval request {approval_id} for tool '{tool_name}' (tenant: {user.tenant_id})")
        return approval_id, token, expires_at

    async def resolve_approval(
        self,
        session: AsyncSession,
        approval_id: str,
        approve: bool,
        acting_user: UserIdentity
    ) -> Tuple[ApprovalRecordModel, Dict[str, Any]]:
        """
        Resolve pending approval request.
        Verifies:
        1. Tenant boundary matching.
        2. Status is PENDING (Replay defense).
        3. Expiration window.
        4. Cryptographic HMAC authenticity.
        """
        stmt = (
            select(ApprovalRecordModel)
            .where(
                ApprovalRecordModel.id == approval_id,
                ApprovalRecordModel.tenant_id == acting_user.tenant_id
            )
            .limit(1)
        )
        res = await session.execute(stmt)
        record = res.scalar_one_or_none()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Approval request {approval_id} not found in tenant {acting_user.tenant_id}."
            )

        now = datetime.datetime.now(datetime.timezone.utc)

        # 1. Replay prevention check
        if record.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Approval request {approval_id} has already been resolved with status: {record.status}."
            )

        # 2. Expiration check
        # Convert record.expires_at to UTC timezone aware if naive
        record_exp = record.expires_at
        if record_exp.tzinfo is None:
            record_exp = record_exp.replace(tzinfo=datetime.timezone.utc)

        if now > record_exp:
            record.status = "EXPIRED"
            await session.commit()
            EIG_APPROVAL_REQUESTS.labels(tool_name=record.tool_name, status="expired").inc()
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Approval request {approval_id} expired at {record_exp.isoformat()}."
            )

        # 3. Cryptographic HMAC verification
        expected_token = self.compute_hmac_token(
            tenant_id=record.tenant_id,
            user_id=record.user_id,
            tool_name=record.tool_name,
            arguments_json=record.arguments_json,
            nonce=record.nonce,
            expires_at=record_exp
        )

        if not hmac.compare_digest(expected_token, record.hmac_token):
            record.status = "TAMPERED"
            await session.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Approval HMAC token verification failed: parameter tampering detected."
            )

        # 4. Finalize resolution
        new_status = "APPROVED" if approve else "REJECTED"
        record.status = new_status
        record.resolved_at = now
        record.resolved_by = acting_user.user_id
        await session.commit()

        EIG_APPROVAL_REQUESTS.labels(tool_name=record.tool_name, status=new_status.lower()).inc()
        logger.info(f"Resolved approval request {approval_id} -> {new_status} by {acting_user.user_id}")

        parsed_args = json.loads(record.arguments_json)
        return record, parsed_args
