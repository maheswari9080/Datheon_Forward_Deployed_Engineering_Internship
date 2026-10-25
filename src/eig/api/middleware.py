"""Application middleware for request correlation, Prometheus metrics, and rate limiting."""

import time
import uuid
from typing import Dict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from eig.core.logging import correlation_id_ctx, logger
from eig.core.metrics import EIG_REQUEST_COUNT, EIG_REQUEST_LATENCY, EIG_ACTIVE_REQUESTS
from eig.config import settings


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assigns or propagates X-Correlation-ID across all requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex[:12]}"
        token = correlation_id_ctx.set(corr_id)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(token)


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Tracks latency and status code distributions for Prometheus scraping."""

    async def dispatch(self, request: Request, call_next) -> Response:
        endpoint = request.url.path
        # Exclude metrics endpoint itself to prevent skew
        if endpoint == "/metrics":
            return await call_next(request)

        EIG_ACTIVE_REQUESTS.inc()
        start_time = time.time()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            raise
        finally:
            duration = time.time() - start_time
            EIG_ACTIVE_REQUESTS.dec()
            EIG_REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            EIG_REQUEST_LATENCY.labels(endpoint=endpoint).observe(duration)


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window request rate limiter per client IP."""

    def __init__(self, app, max_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        super().__init__(app)
        self.max_per_minute = max_per_minute
        self.request_windows: Dict[str, list] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        # Exempt health and metrics from rate limits
        if request.url.path in ["/health/live", "/health/ready", "/metrics"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        timestamps = self.request_windows.get(client_ip, [])
        # Filter timestamps older than 60s
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= self.max_per_minute:
            logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests", "detail": f"Rate limit of {self.max_per_minute}/min exceeded."}
            )

        timestamps.append(now)
        self.request_windows[client_ip] = timestamps

        return await call_next(request)
