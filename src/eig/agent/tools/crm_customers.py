"""CRM customer and lead management tools."""

from typing import Dict, Any, Type
import uuid
from pydantic import BaseModel
from eig.core.security import UserIdentity
from eig.agent.schemas import CustomerLookupArgs, LeadStatusUpdateArgs
from eig.agent.tools.base import BaseEnterpriseTool
from eig.agent.mock_services import mock_enterprise_services


class CustomerLookupTool(BaseEnterpriseTool):
    """Tool for reading customer enterprise profile."""
    name: str = "lookup_customer"
    description: str = "Query customer tier, active contract expiration date, and contact info by customer ID."
    is_write: bool = False
    requires_approval: bool = False
    required_roles = ["sales", "support", "analyst", "admin"]
    args_schema: Type[BaseModel] = CustomerLookupArgs

    async def execute(self, validated_args: CustomerLookupArgs, user: UserIdentity) -> Dict[str, Any]:
        return mock_enterprise_services.lookup_customer(customer_id=validated_args.customer_id)


class UpdateLeadStatusTool(BaseEnterpriseTool):
    """Tool for updating sales pipeline lead state (Requires human approval)."""
    name: str = "update_lead_status"
    description: str = "Transition a sales lead to a new status (e.g. QUALIFIED, WON, LOST). Irreversible write."
    is_write: bool = True
    requires_approval: bool = True
    required_roles = ["sales", "admin"]
    args_schema: Type[BaseModel] = LeadStatusUpdateArgs

    async def execute(self, validated_args: LeadStatusUpdateArgs, user: UserIdentity) -> Dict[str, Any]:
        op_id = f"op_lead_{uuid.uuid4().hex[:8]}"
        return mock_enterprise_services.update_lead_status(
            lead_id=validated_args.lead_id,
            new_status=validated_args.new_status,
            reason=validated_args.reason,
            operation_id=op_id
        )
