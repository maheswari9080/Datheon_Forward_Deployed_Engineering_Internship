"""Base interface and registration contracts for constrained enterprise tools."""

from abc import ABC, abstractmethod
from typing import Type, List, Dict, Any
from pydantic import BaseModel
from eig.core.security import UserIdentity


class BaseEnterpriseTool(ABC):
    """Abstract contract for allowlisted enterprise tools with explicit authorization requirements."""

    name: str
    description: str
    is_write: bool
    requires_approval: bool
    required_roles: List[str]
    args_schema: Type[BaseModel]

    def is_authorized(self, user: UserIdentity) -> bool:
        """Check whether authenticated user possesses any of the required roles."""
        if "admin" in user.roles:
            return True
        return any(role in user.roles for role in self.required_roles)

    @abstractmethod
    async def execute(self, validated_args: BaseModel, user: UserIdentity) -> Dict[str, Any]:
        """Execute the verified tool action against underlying ERP/CRM mock service."""
        pass
