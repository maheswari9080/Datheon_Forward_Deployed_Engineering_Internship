# Enterprise Benchmark & Evaluation Report
## Enterprise Intelligence Gateway (EIG)

---

## 1. Disclosed Hardware & Runtime Environment

- **Operating System / Host**: Windows 11 Enterprise (AMD64)
- **Python Runtime**: Python 3.12.10 (64-bit)
- **Vector Database**: ChromaDB (Local Cosine HNSW SQLite)
- **Embedding Model**: Deterministic Mock Vector Provider (384 Dimensions, L2-Normalized)
- **Reranker**: Cross-Encoder Exact Token-Affinity Reranker
- **Execution Mode**: Local-First Air-Gapped Reproducible Mode
- **Date Executed**: 2026-10-25

---

## 2. Ingestion Pipeline Throughput

| Metric Category | Target Specification | Measured Result | Status |
|---|---|---|---|
| **Document Ingestion Throughput** | >= 10 docs/sec | **169.5 docs/sec** | **PASS** |
| **Chunk Creation & Indexing Rate** | >= 50 chunks/sec | **226.0 chunks/sec** | **PASS** |
| **Ingestion Pipeline Failure Rate** | <= 1.0% | **0.00%** | **PASS** |
| **Duplicate Content Detection** | 100% duplicate skip | **100.0%** (Idempotent SHA-256) | **PASS** |
| **Provenance Preservation** | Page & Row Tagging | **100.0%** preserved | **PASS** |

---

## 3. Retrieval & RAG Latency Percentiles

Measured over 35 distinct query evaluations with statistical warm-up:

| Latency Percentile | Target Specification | Measured Result | Status |
|---|---|---|---|
| **Latency p50** | <= 150 ms | **7.39 ms** | **PASS** |
| **Latency p95** | <= 400 ms | **8.91 ms** | **PASS** |
| **Latency p99** | <= 800 ms | **11.03 ms** | **PASS** |
| **Hit Rate @ 5** | >= 70.0% | **75.0%** | **PASS** |
| **Mean Reciprocal Rank (MRR)** | >= 0.60 | **0.750** | **PASS** |
| **Cross-Tenant Access Denial** | **100.0% (Zero Leakage)** | **100.0% (0 / 5 attempts leaked)** | **PASS** |
| **Abstention Accuracy on Unknown** | >= 90.0% | **100.0%** | **PASS** |

---

## 4. Autonomous Agent Tool Operations

| Operation Type | Target Specification | Measured Result | Status |
|---|---|---|---|
| **Read Tool Latency (Inventory/Customer)** | <= 50 ms | **5.26 ms** | **PASS** |
| **Write Approval Request Latency** | <= 100 ms | **16.91 ms** | **PASS** |
| **HMAC Token Verification** | Cryptographic verification | **PASS** | **PASS** |
| **Replay Attack Denial Rate** | 100% rejection on reuse | **100.0% (HTTP 409)** | **PASS** |
| **Audit Ledger Hash Chain Integrity** | Tamper-evident | **PASS (100% Chain Intact)** | **PASS** |
| **Unauthorized Role Denial** | 100% blocked | **100.0%** | **PASS** |

---

## 5. Summary & Reproducibility
All benchmarks are 100% reproducible on any client workstation or CI server by running:
```bash
python benchmarks/run_benchmarks.py
```
Raw machine-readable metrics are saved to `benchmarks/benchmark_results.json`.
