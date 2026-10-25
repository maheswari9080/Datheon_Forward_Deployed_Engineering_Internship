"""Agent execution and tool orchestration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from eig.core.database import get_db
from eig.core.security import UserIdentity, get_current_user
from eig.agent.schemas import AgentTaskRequest, AgentTaskResponse
from eig.agent.orchestrator import AgentOrchestrator

agent_router = APIRouter(prefix="/agent", tags=["Autonomous ERP/CRM Agent"])
agent_orchestrator = AgentOrchestrator()


@agent_router.post("/execute", response_model=AgentTaskResponse, summary="Execute Autonomous Agent Task")
async def execute_agent_task(
    request: AgentTaskRequest,
    user: UserIdentity = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute constrained agent workflow:
    PLAN -> VALIDATE -> AUTHORIZE -> APPROVE -> EXECUTE -> VERIFY -> AUDIT.
    Sensitive writes return APPROVAL_REQUIRED with cryptographic approval token.
    """
    return await agent_orchestrator.execute_task(session=db, request=request, user=user)
