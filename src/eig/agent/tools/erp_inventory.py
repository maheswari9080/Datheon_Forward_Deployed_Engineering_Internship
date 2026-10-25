"""Inventory lookup tool."""

from typing import Dict, Any, Type
from pydantic import BaseModel
from eig.core.security import UserIdentity
from eig.agent.schemas import InventoryLookupArgs
from eig.agent.tools.base import BaseEnterpriseTool
from eig.agent.mock_services import mock_enterprise_services


class InventoryLookupTool(BaseEnterpriseTool):
    """Tool for querying warehouse stock levels."""
    name: str = "lookup_inventory"
    description: str = "Query stock quantities, unit pricing, and warehouse locations by SKU."
    is_write: bool = False
    requires_approval: bool = False
    required_roles = ["inventory", "operations", "viewer", "analyst", "admin"]
    args_schema: Type[BaseModel] = InventoryLookupArgs

    async def execute(self, validated_args: InventoryLookupArgs, user: UserIdentity) -> Dict[str, Any]:
        return mock_enterprise_services.lookup_inventory(
            sku=validated_args.sku,
            location_id=validated_args.location_id
        )
