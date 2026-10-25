# REST API Integration Guide
## Enterprise Intelligence Gateway (EIG)

---

## 1. Authentication

All protected endpoints require an enterprise JSON Web Token (JWT) provided in the `Authorization` header:
```http
Authorization: Bearer <TOKEN>
```

### Issue Authentication Token
**`POST /api/v1/auth/token`**
```json
{
  "user_id": "usr_alice",
  "tenant_id": "tenant_megacorp",
  "username": "alice.smith",
  "roles": ["analyst", "engineering"],
  "departments": ["engineering"],
  "clearance_level": 2
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "tenant_id": "tenant_megacorp",
  "expires_in_minutes": 60
}
```

---

## 2. Document Ingestion

### Upload Document
**`POST /api/v1/ingest/upload`** (Multipart Form)
- `file`: Binary file stream (`.pdf`, `.csv`, `.md`)
- `department`: Business unit (e.g. `engineering`)
- `access_tier`: Integer 1-5
- `document_date`: Optional ISO date (`YYYY-MM-DD`)

**Response (200 OK):**
```json
{
  "document_id": "7fae2981bc92a8e7",
  "filename": "security_architecture.pdf",
  "tenant_id": "tenant_megacorp",
  "department": "engineering",
  "access_tier": 2,
  "chunks_indexed": 6,
  "is_duplicate": false,
  "status": "INDEXED"
}
```

---

## 3. RAG Q&A with Citations

### Execute Query
**`POST /api/v1/rag/query`**
```json
{
  "query": "What are the requirements for production deployments?",
  "top_k": 5,
  "enable_reranking": true
}
```
**Response (200 OK):**
```json
{
  "query": "What are the requirements for production deployments?",
  "answer": "Based on the authorized enterprise records:\n\n[security_architecture.pdf | Page 2 | ID: 7fae2981bc92a8e7_1]\nAll production deployments must pass automated SAST and approval checks.\n\nSources Verified: 1 citation(s).",
  "citations": [
    {
      "document_name": "security_architecture.pdf",
      "page_number": 2,
      "row_number": null,
      "section_header": "Page 2",
      "chunk_id": "7fae2981bc92a8e7_1",
      "snippet": "All production deployments must pass automated SAST and approval checks..."
    }
  ],
  "insufficient_evidence": false,
  "chunks_evaluated": 1,
  "execution_time_seconds": 0.045
}
```

---

## 4. Autonomous Agent Execution & Approvals

### Execute Agent Task
**`POST /api/v1/agent/execute`**
```json
{
  "prompt": "Update lead LEAD-4891 to QUALIFIED status",
  "tool_name": "update_lead_status",
  "tool_arguments": {
    "lead_id": "LEAD-4891",
    "new_status": "QUALIFIED",
    "reason": "Scoping requirements verified with lead architect"
  }
}
```
**Response (200 OK - Approval Required):**
```json
{
  "task_id": "task_92fa71",
  "action_taken": "update_lead_status",
  "outcome": "APPROVAL_REQUIRED",
  "trace": [
    {"phase": "PLAN", "details": "Identified operation 'update_lead_status' (Write).", "status": "SUCCESS"},
    {"phase": "VALIDATE", "details": "Tool arguments successfully validated against LeadStatusUpdateArgs.", "status": "SUCCESS"},
    {"phase": "AUTHORIZE", "details": "User 'usr_alice' authorized for tool 'update_lead_status'.", "status": "SUCCESS"},
    {"phase": "REQUEST_APPROVAL", "details": "Tool is an irreversible write requiring human approval.", "status": "PENDING_APPROVAL"}
  ],
  "approval_request_id": "appr_7c81a293",
  "result": {
    "message": "Operation requires human approval before execution.",
    "approval_id": "appr_7c81a293",
    "tool": "update_lead_status"
  }
}
```

### Approve and Execute Write
**`POST /api/v1/approvals/{approval_id}/approve`**
**Response (200 OK):**
```json
{
  "task_id": "task_appr_appr_7c81a293",
  "action_taken": "update_lead_status",
  "outcome": "COMPLETED",
  "result": {
    "success": true,
    "operation_id": "op_lead_4819a",
    "lead_id": "LEAD-4891",
    "previous_status": "CONTACTED",
    "new_status": "QUALIFIED"
  }
}
```

---

## 5. Health & Monitoring

- **`GET /health/live`**: Process liveness probe.
- **`GET /health/ready`**: Backing database & vector connectivity check.
- **`GET /metrics`**: Prometheus metrics scrape endpoint.
- **`GET /api/v1/diagnostics/config`**: Sanitized operational settings inspection.
- **`GET /api/v1/diagnostics/audit-integrity`**: Cryptographic hash chain validation of audit ledger.
