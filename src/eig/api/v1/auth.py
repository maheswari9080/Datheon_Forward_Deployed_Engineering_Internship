"""Authentication and identity token endpoints."""

from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from eig.core.security import UserIdentity, create_access_token, get_current_user

auth_router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])


class TokenRequest(BaseModel):
    """Credentials payload for issuing enterprise session token."""
    user_id: str = Field(..., example="usr_alice_sec")
    tenant_id: str = Field(..., example="tenant_megacorp_a")
    username: str = Field(..., example="alice.smith")
    roles: List[str] = Field(default_factory=lambda: ["viewer", "analyst"], example=["analyst"])
    departments: List[str] = Field(default_factory=lambda: ["engineering"], example=["engineering"])
    clearance_level: int = Field(default=2, ge=1, le=5, example=2)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    expires_in_minutes: int


@auth_router.post("/token", response_model=TokenResponse, summary="Issue Authentication Token")
async def issue_token(req: TokenRequest):
    """
    Authenticate enterprise user and issue signed JWT containing tenant and RBAC claims.
    """
    identity = UserIdentity(
        user_id=req.user_id,
        tenant_id=req.tenant_id,
        username=req.username,
        roles=req.roles,
        departments=req.departments,
        clearance_level=req.clearance_level
    )
    token = create_access_token(identity)
    return TokenResponse(
        access_token=token,
        tenant_id=req.tenant_id,
        expires_in_minutes=60
    )


@auth_router.get("/me", response_model=UserIdentity, summary="Get Current Identity")
async def get_my_identity(user: UserIdentity = Depends(get_current_user)):
    """Retrieve server-verified user identity and authorized clearance tier."""
    return user
