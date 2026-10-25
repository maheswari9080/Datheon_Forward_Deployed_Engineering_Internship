# ==============================================================================
# Enterprise Intelligence Gateway (EIG) - Multi-Stage Production Dockerfile
# Security Hardened: Non-root execution, minimal attack surface, reproducible build
# ==============================================================================

# Stage 1: Build stage with compiler toolchain
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Hardened Runtime stage
FROM python:3.12-slim-bookworm AS runtime

LABEL maintainer="Forward Deployed Engineering Team <fde@datheon.ai>"
LABEL description="Enterprise Intelligence Gateway - Production Secure Microservice"

# Create non-root system user with explicit UID/GID
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install minimal runtime utilities (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed python wheels from builder to appuser home
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app/src

# Create application data directories with non-root ownership
RUN mkdir -p /app/data /app/data/chroma_db && \
    chown -R appuser:appgroup /app /home/appuser

# Copy application source code
COPY --chown=appuser:appgroup pyproject.toml .
COPY --chown=appuser:appgroup src/ /app/src/
COPY --chown=appuser:appgroup data/synthetic/ /app/data/synthetic/

# Switch to unprivileged runtime user
USER appuser:appgroup

# Expose HTTP port
EXPOSE 8000

# Container Healthcheck (Liveness probe)
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Graceful shutdown signal
STOPSIGNAL SIGTERM

# Run FastAPI microservice via Uvicorn
CMD ["uvicorn", "eig.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--access-log"]
