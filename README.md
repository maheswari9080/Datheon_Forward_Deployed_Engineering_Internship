# Enterprise Intelligence Gateway (EIG)

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Security](https://img.shields.io/badge/Security-Fail--Closed_RBAC-success.svg)](SECURITY.md)

**Enterprise Intelligence Gateway (EIG)** is an execution-ready, secure enterprise AI platform that integrates legacy document ingestion, multi-tenant RBAC retrieval-augmented generation (RAG), autonomous ERP/CRM tool orchestration with human-in-the-loop approvals, and containerized microservice observability.

---

## 🌟 Key Features

1. **Legacy Document Ingestion & Vector ETL**:
   - Extract text from **PDFs** (with page-level provenance), **CSVs** (row-level traceability), and **Markdown** (AST heading trees).
   - Idempotent deduplication via deterministic SHA-256 content hashes.
   - Local ChromaDB vector storage with cosine similarity and optional Qdrant adapter.
   - Local-first embedding provider with deterministic fallback for air-gapped environments.

2. **Multi-Tenant Secure RAG with RBAC**:
   - Server-verified identity and tenant isolation derived strictly from server-side JWT context.
   - Pre-retrieval metadata filtering combined with post-retrieval fail-closed revalidation.
   - Hybrid retrieval (Sparse BM25 + Dense Cosine Vector) merged via Reciprocal Rank Fusion (RRF).
   - Cross-encoder reranking and context-window budgeting.
   - Grounded citations: `[Document Name | Page X / Row Y | ID: chunk_id]`.
   - Explicit `INSUFFICIENT_EVIDENCE` abstention response when confidence is below threshold.
   - Untrusted evidence boundary isolation and prompt injection defense.

3. **Autonomous ERP/CRM Agent**:
   - Strict execution flow: `PLAN -> VALIDATE -> AUTHORIZE -> APPROVE -> EXECUTE -> VERIFY -> AUDIT`.
   - Allowlisted tools: Inventory lookup, customer lookup, lead status update, support ticket filing, operation verification.
   - Cryptographic HMAC-SHA256 human-in-the-loop approval engine with single-use nonces and expiration TTL.
   - Append-only cryptographic hash chain audit logging with tamper verification.

4. **Production Microservice & Observability**:
   - High-throughput asynchronous FastAPI backend.
   - Liveness (`/health/live`) and Readiness (`/health/ready`) probes.
   - Prometheus metrics exposition (`/metrics`) with zero high-cardinality label explosions.
   - Request correlation IDs (`X-Correlation-ID`) and in-memory rate limiting.
   - Multi-stage hardened non-root `Dockerfile` and `docker-compose.yml`.

---

## 🚀 Quick Start (Local-First)

### 1. Installation
Clone the repository and install dependencies in Python 3.12:
```bash
git clone git@github-maheswari:maheswari9080/Datheon_Forward_Deployed_Engineering_Internship.git
cd Datheon_Forward_Deployed_Engineering_Internship/mw
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```

### 3. Run Automated Test Suite
```bash
python -m pytest tests/ -v
```

### 4. Execute Benchmark Suite
```bash
python benchmarks/run_benchmarks.py
```

### 5. Launch Gateway Service
```bash
uvicorn eig.main:app --host 0.0.0.0 --port 8000 --reload
```
Navigate to `http://localhost:8000/docs` to view interactive OpenAPI Swagger documentation.

---

## 🐳 Docker Deployment

To launch the complete application stack using Docker Compose:
```bash
docker compose up -d --build
```
Verify container health:
```bash
curl http://localhost:8000/health/ready
```

---

## 📚 Technical Documentation Suite

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture, data flow, trust boundaries, design tradeoffs.
- [SECURITY.md](SECURITY.md) - Threat model, 10 security invariants, RBAC clearance enforcement.
- [API_GUIDE.md](API_GUIDE.md) - REST API specifications, authentication, sample payloads.
- [CLIENT_INTEGRATION_GUIDE.md](CLIENT_INTEGRATION_GUIDE.md) - Enterprise integration, IAM, VPC controls.
- [BENCHMARK_REPORT.md](BENCHMARK_REPORT.md) - Ingestion throughput, p50/p95/p99 latency, HitRate@5.
- [TEST_REPORT.md](TEST_REPORT.md) - 23 automated tests, 14 test categories, pass/fail status.
- [RUNBOOK.md](RUNBOOK.md) - Startup, shutdown, recovery, backup, and data deletion procedures.
