# System Architecture & Design Decisions
## Enterprise Intelligence Gateway (EIG)

---

## 1. Executive Architecture Summary

Enterprise Intelligence Gateway is architected as an asynchronous, local-first modular monolith built in Python 3.12+ and FastAPI. It integrates document ingestion, multi-tenant hybrid retrieval, autonomous ERP/CRM tool execution, and observability into a unified trust boundary.

```mermaid
flowchart TD
    subgraph ClientZone [Client Integration Zone]
        ClientApp[Enterprise Web / ERP Client]
    end

    subgraph GatewayBoundary [Trust Boundary: FastAPI Gateway (Module 4)]
        AuthGuard[Auth Middleware / JWT Verification]
        RateLimit[Rate Limiter & Correlation ID]
        Router[API Routing Layer]
        Metrics[Prometheus Registry]
    end

    subgraph IngestionBoundary [ETL Pipeline: Module 1]
        ParserFactory[Format Parsers: PDF, CSV, Markdown]
        Chunker[Structure & Heading Aware Chunker]
        Hasher[SHA-256 Deduplication]
    end

    subgraph RAGBoundary [Secure Multi-Tenant RAG: Module 2]
        ACLFilter[Pre-Retrieval RBAC / Clearance Filter]
        Hybrid[Hybrid Retriever: BM25 + Cosine Vector]
        RRF[Reciprocal Rank Fusion]
        Rerank[Cross-Encoder Reranker]
        Budget[Context Window Budgeter]
        Synthesis[Grounded Generator & Citation Formatter]
    end

    subgraph AgentBoundary [Autonomous Agent: Module 3]
        StateOrch[Orchestrator: PLAN -> VALIDATE -> AUTHORIZE]
        Approval[HMAC-SHA256 Approval Engine]
        MockServices[Mock ERP/CRM Services]
        AuditTrail[Append-Only Hash Chain Ledger]
    end

    subgraph StorageBoundary [Persistent Storage Layer]
        SQLiteDB[(SQLite / PostgreSQL Metadata & Audit)]
        VectorDB[(ChromaDB / Qdrant Vector Index)]
    end

    ClientApp --> AuthGuard
    AuthGuard --> RateLimit --> Router
    Router --> IngestionBoundary
    Router --> RAGBoundary
    Router --> AgentBoundary
    IngestionBoundary --> VectorDB
    IngestionBoundary --> SQLiteDB
    RAGBoundary --> VectorDB
    AgentBoundary --> Approval --> MockServices
    AgentBoundary --> AuditTrail --> SQLiteDB
    Router --> Metrics
```

---

## 2. Core Architectural Decisions

### Decision 1: Server-Verified Tenant Identity Context
- **Context**: Multi-tenant systems frequently suffer from IDOR (Insecure Direct Object Reference) vulnerabilities when tenant IDs are passed as query parameters or extracted from LLM prompt responses.
- **Decision**: In EIG, tenant identity is strictly extracted from server-verified cryptographic JWT tokens via the `get_current_user` dependency. Any tenant ID supplied by the client in body parameters or prompt arguments is ignored.

### Decision 2: Pre-Retrieval RBAC Filtering with Fail-Closed Revalidation
- **Context**: Relying on LLMs to enforce document access control is ineffective and vulnerable to prompt injection.
- **Decision**: Vector database queries enforce pre-retrieval where filters (`tenant_id == user.tenant_id`, `department IN user.departments`, `access_tier <= user.clearance_level`). A secondary post-retrieval validation gate ensures that any unexpected vector store leakage immediately causes the engine to fail closed.

### Decision 3: Hybrid Search (BM25 + Dense Cosine Vector) with RRF
- **Context**: Dense vector embeddings struggle with exact product SKUs, serial numbers, and specialized acronyms, while keyword search struggles with conceptual semantics.
- **Decision**: Hybrid search executes dense cosine similarity alongside BM25 lexical tokenization, merging candidate ranks using Reciprocal Rank Fusion:
  $$RRF(d) = \sum_{m \in \{dense, sparse\}} \frac{1}{60 + \text{rank}_m(d)}$$

### Decision 4: Cryptographic Human Approval for Irreversible Writes
- **Context**: Autonomous LLM agents must not execute sensitive write operations without human confirmation.
- **Decision**: All write operations (e.g. updating CRM leads, filing support tickets) generate an `ApprovalRequest` protected by an HMAC-SHA256 signature binding the tenant ID, user ID, tool name, argument hash, and expiration timestamp. Nonces prevent replay attacks.

### Decision 5: Append-Only Audit Trail with Hash Chaining
- **Context**: Regulatory audits require proof that logs have not been tampered with or retroactively altered.
- **Decision**: Each audit entry stores `prev_hash` and `current_hash = SHA256(prev_hash + tenant_id + user_id + action + resource + details + timestamp)`. Any alteration breaks the cryptographic verification chain.
