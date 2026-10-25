"""FastAPI Application entrypoint and lifecycle coordinator for Enterprise Intelligence Gateway."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from eig.config import settings
from eig.core.database import init_db
from eig.core.logging import logger
from eig.api.middleware import (
    CorrelationIdMiddleware,
    PrometheusMetricsMiddleware,
    InMemoryRateLimitMiddleware,
)
from eig.api.health import health_router
from eig.api.v1.auth import auth_router
from eig.api.v1.ingestion import ingestion_router
from eig.api.v1.search import search_router
from eig.api.v1.rag import rag_router
from eig.api.v1.agent import agent_router
from eig.api.v1.approvals import approvals_router
from eig.api.v1.operations import operations_router
from eig.api.v1.diagnostics import diagnostics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and graceful shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    await init_db()
    logger.info("SQL database schema initialized successfully")
    yield
    logger.info("Graceful shutdown initiated. Cleaning up resources.")


def create_application() -> FastAPI:
    """Build and configure production FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description="Unified Enterprise AI Integration Platform - Ingestion, Multi-Tenant RAG, Autonomous Agent",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )

    # Core Middleware Stack (Ordered)
    app.add_middleware(InMemoryRateLimitMiddleware)
    app.add_middleware(PrometheusMetricsMiddleware)
    app.add_middleware(CorrelationIdMiddleware)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.ENVIRONMENT == "development" else ["https://corp.enterprise.local"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Mount Base Health & Metrics
    app.include_router(health_router)

    # Mount API v1 Routers
    v1_prefix = settings.API_V1_STR
    app.include_router(auth_router, prefix=v1_prefix)
    app.include_router(ingestion_router, prefix=v1_prefix)
    app.include_router(search_router, prefix=v1_prefix)
    app.include_router(rag_router, prefix=v1_prefix)
    app.include_router(agent_router, prefix=v1_prefix)
    app.include_router(approvals_router, prefix=v1_prefix)
    app.include_router(operations_router, prefix=v1_prefix)
    app.include_router(diagnostics_router, prefix=v1_prefix)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("eig.main:app", host="0.0.0.0", port=8000, reload=True)
