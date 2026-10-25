"""Support ticket creation, status inspection, and operation verification tools."""

from typing import Dict, Any, Type
import uuid
from pydantic import BaseModel
from eig.core.security import UserIdentity
from eig.agent.schemas import CreateSupportTicketArgs, TicketStatusLookupArgs, OperationVerificationArgs
from eig.agent.tools.base import BaseEnterpriseTool
from eig.agent.mock_services import mock_enterprise_services


class CreateSupportTicketTool(BaseEnterpriseTool):
    """Tool for filing enterprise support tickets (Requires human approval)."""
    name: str = "create_support_ticket"
    description: str = "Create a new customer incident support ticket with assigned severity. Irreversible write."
    is_write: bool = True
    requires_approval: bool = True
    required_roles = ["support", "operations", "admin"]
    args_schema: Type[BaseModel] = CreateSupportTicketArgs

    async def execute(self, validated_args: CreateSupportTicketArgs, user: UserIdentity) -> Dict[str, Any]:
        op_id = f"op_tick_{uuid.uuid4().hex[:8]}"
        return mock_enterprise_services.create_support_ticket(
            customer_id=validated_args.customer_id,
            priority=validated_args.priority,
            description=validated_args.issue_description,
            operation_id=op_id
        )


class TicketStatusLookupTool(BaseEnterpriseTool):
    """Tool for reading support ticket state."""
    name: str = "lookup_ticket_status"
    description: str = "Query current resolution status of an enterprise support ticket by ticket ID."
    is_write: bool = False
    requires_approval: bool = False
    required_roles = ["support", "operations", "viewer", "analyst", "admin"]
    args_schema: Type[BaseModel] = TicketStatusLookupArgs

    async def execute(self, validated_args: TicketStatusLookupArgs, user: UserIdentity) -> Dict[str, Any]:
        return mock_enterprise_services.lookup_ticket_status(ticket_id=validated_args.ticket_id)


class VerifyOperationStatusTool(BaseEnterpriseTool):
    """Tool for verifying outcome of previously submitted operation."""
    name: str = "verify_operation_status"
    description: str = "Verify the execution status and outcome of an asynchronous or prior operation ID."
    is_write: bool = False
    requires_approval: bool = False
    required_roles = ["support", "operations", "viewer", "analyst", "admin"]
    args_schema: Type[BaseModel] = OperationVerificationArgs

    async def execute(self, validated_args: OperationVerificationArgs, user: UserIdentity) -> Dict[str, Any]:
        return mock_enterprise_services.verify_operation_status(operation_id=validated_args.operation_id)
