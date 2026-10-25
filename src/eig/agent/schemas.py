"""Typed Pydantic schemas for agent tool arguments, plans, and execution traces."""

from typing import Optional, Literal, Dict, Any, List
from pydantic import BaseModel, Field


class InventoryLookupArgs(BaseModel):
    """Parameters for looking up item inventory across enterprise warehouses."""
    sku: str = Field(..., min_length=3, max_length=64, description="Stock Keeping Unit identifier")
    location_id: Optional[str] = Field(default=None, description="Specific warehouse or regional DC ID")


class CustomerLookupArgs(BaseModel):
    """Parameters for querying CRM customer details."""
    customer_id: str = Field(..., min_length=3, max_length=64, description="Enterprise CRM customer identifier")


class LeadStatusUpdateArgs(BaseModel):
    """Parameters for updating sales lead state (Irreversible write operation)."""
    lead_id: str = Field(..., min_length=3, max_length=64, description="Target CRM lead ID")
    new_status: Literal["CONTACTED", "QUALIFIED", "UNQUALIFIED", "PROPOSAL_SENT", "WON", "LOST"] = Field(
        ..., description="Target business lifecycle state"
    )
    reason: str = Field(..., min_length=5, max_length=500, description="Audit justification for state transition")


class CreateSupportTicketArgs(BaseModel):
    """Parameters for filing enterprise support ticket (Irreversible write operation)."""
    customer_id: str = Field(..., min_length=3, max_length=64, description="Account customer identifier")
    priority: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = Field(default="MEDIUM", description="Incident severity")
    issue_description: str = Field(..., min_length=10, max_length=2000, description="Detailed fault summary")


class TicketStatusLookupArgs(BaseModel):
    """Parameters for retrieving support ticket lifecycle status."""
    ticket_id: str = Field(..., min_length=3, max_length=64, description="Support ticket tracking ID")


class OperationVerificationArgs(BaseModel):
    """Parameters for verifying state and outcome of previously submitted operation."""
    operation_id: str = Field(..., min_length=3, max_length=128, description="Cryptographic operation tracking ID")


class AgentExecutionStep(BaseModel):
    """Step record within the readable action/observation trace."""
    phase: Literal["PLAN", "VALIDATE", "AUTHORIZE", "REQUEST_APPROVAL", "EXECUTE", "VERIFY", "AUDIT"]
    details: str
    status: Literal["SUCCESS", "FAILED", "PENDING_APPROVAL", "BLOCKED"]
    data: Optional[Dict[str, Any]] = None


class AgentTaskRequest(BaseModel):
    """High-level user request submitted to the agent."""
    prompt: str = Field(..., min_length=3, max_length=2000, description="Natural language enterprise instruction")
    tool_name: Optional[str] = Field(default=None, description="Explicit tool name if direct execution")
    tool_arguments: Optional[Dict[str, Any]] = Field(default=None, description="Direct tool argument payload")
    idempotency_key: Optional[str] = Field(default=None, description="Client idempotency key for safe retries")


class AgentTaskResponse(BaseModel):
    """Result of agent orchestration flow."""
    task_id: str
    action_taken: str
    outcome: Literal["COMPLETED", "APPROVAL_REQUIRED", "FAILED", "UNAUTHORIZED"]
    trace: List[AgentExecutionStep]
    result: Optional[Dict[str, Any]] = None
    approval_request_id: Optional[str] = None
    execution_time_seconds: float = 0.0
