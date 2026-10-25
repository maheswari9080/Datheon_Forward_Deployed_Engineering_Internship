"""Health checks (Liveness & Readiness) and Prometheus metrics exposition."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from eig.core.database import get_db
from eig.core.metrics import get_metrics_exposition
from eig.config import settings

health_router = APIRouter(tags=["Health & Monitoring"])


@health_router.get("/health/live", summary="Liveness Probe")
async def liveness_probe():
    """Verify application process is responsive."""
    return {"status": "alive", "app": settings.APP_NAME, "version": settings.VERSION}


@health_router.get("/health/ready", summary="Readiness Probe")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """Verify backing storage and database connectivity."""
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unavailable"}
        )

    return {
        "status": "ready",
        "database": "connected",
        "vector_store": settings.VECTOR_STORE_PROVIDER,
        "environment": settings.ENVIRONMENT
    }


@health_router.get("/metrics", summary="Prometheus Metrics")
async def prometheus_metrics():
    """Expose Prometheus formatted telemetry."""
    data, content_type = get_metrics_exposition()
    return Response(content=data, media_type=content_type)
