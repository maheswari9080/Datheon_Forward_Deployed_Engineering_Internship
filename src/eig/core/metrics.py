"""Prometheus metrics instrumentation avoiding high-cardinality labels."""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# HTTP Request Metrics
EIG_REQUEST_COUNT = Counter(
    "eig_requests_total",
    "Total HTTP requests received",
    ["method", "endpoint", "status_code"]
)

EIG_REQUEST_LATENCY = Histogram(
    "eig_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

EIG_ACTIVE_REQUESTS = Gauge(
    "eig_active_requests",
    "Current active in-flight HTTP requests"
)

# Ingestion Pipeline Metrics
EIG_INGESTION_DOCS = Counter(
    "eig_ingestion_documents_total",
    "Total ingested documents by file format and outcome",
    ["file_type", "status"]
)

EIG_INGESTION_CHUNKS = Counter(
    "eig_ingestion_chunks_total",
    "Total document chunks created and indexed",
    ["status"]
)

EIG_INGESTION_DURATION = Histogram(
    "eig_ingestion_duration_seconds",
    "Time taken for document ingestion and indexing pipeline",
    ["stage"],
    buckets=[0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 15.0, 30.0]
)

# RAG & Retrieval Metrics
EIG_RETRIEVAL_LATENCY = Histogram(
    "eig_retrieval_duration_seconds",
    "Latency of hybrid and vector retrieval",
    ["retriever_type"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

EIG_RERANK_LATENCY = Histogram(
    "eig_reranking_duration_seconds",
    "Latency of cross-encoder reranking step",
    ["status"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

EIG_RAG_QUERIES = Counter(
    "eig_rag_queries_total",
    "Total RAG generation requests by outcome category",
    ["outcome"]  # grounded, insufficient_evidence, error, rejected_injection
)

# Agent Tool & Approval Metrics
EIG_AGENT_TOOL_CALLS = Counter(
    "eig_agent_tool_calls_total",
    "Total agent tool executions by tool and outcome",
    ["tool_name", "outcome"]  # success, failure, unauthorized, approval_required
)

EIG_APPROVAL_REQUESTS = Counter(
    "eig_approval_requests_total",
    "Total human-in-the-loop approval actions",
    ["tool_name", "status"]  # created, approved, rejected, expired
)


def get_metrics_exposition() -> tuple[bytes, str]:
    """Return raw bytes and content type for Prometheus scrape endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
