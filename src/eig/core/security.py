"""Enterprise security models, JWT handling, and tenant context enforcement."""

import datetime
from typing import List, Optional, Dict, Any
import jwt
from pydantic import BaseModel, Field
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from eig.config import settings

security_bearer = HTTPBearer(auto_error=False)


class UserIdentity(BaseModel):
    """Verified enterprise user identity extracted from cryptographic authentication credentials."""
    user_id: str = Field(..., description="Unique user identifier")
    tenant_id: str = Field(..., description="Enterprise tenant boundary")
    username: str = Field(..., description="Corporate username")
    roles: List[str] = Field(default_factory=lambda: ["viewer"], description="RBAC roles")
    departments: List[str] = Field(default_factory=list, description="Authorized departments")
    clearance_level: int = Field(default=1, ge=1, le=5, description="Security clearance tier (1-5)")

    def can_access_department(self, department: str) -> bool:
        """Verify whether user holds permission for a given department."""
        if "admin" in self.roles:
            return True
        return department.lower() in [d.lower() for d in self.departments]

    def can_access_clearance(self, tier: int) -> bool:
        """Check whether user clearance satisfies document access tier."""
        return self.clearance_level >= tier


class TokenPayload(BaseModel):
    """Payload schema encoded within enterprise JWT."""
    sub: str
    tenant_id: str
    username: str
    roles: List[str]
    departments: List[str]
    clearance_level: int
    exp: datetime.datetime
    iat: datetime.datetime


def create_access_token(
    user: UserIdentity,
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """Issue a cryptographically signed JWT for the authenticated user identity."""
    now = datetime.datetime.now(datetime.timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user.user_id,
        "tenant_id": user.tenant_id,
        "username": user.username,
        "roles": user.roles,
        "departments": user.departments,
        "clearance_level": user.clearance_level,
        "exp": expire,
        "iat": now,
    }
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> UserIdentity:
    """Decode and strictly validate JWT token, returning the trusted UserIdentity."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return UserIdentity(
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            username=payload["username"],
            roles=payload.get("roles", ["viewer"]),
            departments=payload.get("departments", []),
            clearance_level=payload.get("clearance_level", 1)
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, KeyError, Exception) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> UserIdentity:
    """
    FastAPI security dependency to extract and verify the current user identity.
    Enforces Security Invariant #1: Identity is ALWAYS derived from trusted server-side context.
    Enforces Security Invariant #4: Fail-closed if credentials are missing or invalid.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return verify_token(credentials.credentials)
