# Enterprise Operations Runbook
## Enterprise Intelligence Gateway (EIG)

---

## 1. Service Startup Procedures

### Local Development / Evaluation Startup
```powershell
# Set Python path and launch Uvicorn development server
$env:PYTHONPATH="src"
uvicorn eig.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production Docker Container Startup
```bash
# Build and launch with healthcheck validation
docker compose up -d --build
docker compose ps
curl -f http://localhost:8000/health/ready
```

---

## 2. Graceful Shutdown & Recovery Procedures

### Graceful Shutdown
The application listens for `SIGTERM` and `SIGINT` signals. Upon receiving a termination signal, Uvicorn drains active in-flight requests and closes database sessions cleanly:
```bash
docker compose down
```

### Crash Recovery Procedure
If the application exits unexpectedly:
1. Inspect last 100 log lines:
   ```bash
   docker logs --tail 100 eig-gateway-service
   ```
2. Verify SQLite / PostgreSQL database locks:
   ```bash
   sqlite3 ./data/eig.db "PRAGMA integrity_check;"
   ```
3. Restart container service:
   ```bash
   docker compose restart eig-gateway
   ```

---

## 3. Backup & Disaster Recovery (DR)

### Backup Procedure
Execute scheduled hot backup of the metadata registry and ChromaDB persistent directory:
```bash
# Snapshot SQLite database safely using vacuum into
sqlite3 ./data/eig.db "VACUUM INTO './data/backups/eig_backup_$(date +%F).db';"

# Archive ChromaDB persistent index
tar -czf ./data/backups/chroma_backup_$(date +%F).tar.gz ./data/chroma_db/
```

### Restore Procedure
1. Stop running gateway instances.
2. Restore SQLite database:
   ```bash
   cp ./data/backups/eig_backup_TARGET.db ./data/eig.db
   ```
3. Extract ChromaDB index:
   ```bash
   rm -rf ./data/chroma_db/*
   tar -xzf ./data/backups/chroma_backup_TARGET.tar.gz -C ./
   ```
4. Verify audit ledger chain integrity:
   ```bash
   curl -H "Authorization: Bearer <ADMIN_TOKEN>" http://localhost:8000/api/v1/diagnostics/audit-integrity
   ```
5. Restart service.

---

## 4. Tenant Data Deletion & Purge Runbook

Under GDPR / CCPA right-to-be-forgotten mandates, to completely purge all records for a specific tenant:

```bash
# 1. Query all documents belonging to tenant via REST API
curl -X GET -H "Authorization: Bearer <TENANT_ADMIN_TOKEN>" http://localhost:8000/api/v1/ingest/documents

# 2. Issue deletion for each document ID (purges vector store and updates registry)
curl -X DELETE -H "Authorization: Bearer <TENANT_ADMIN_TOKEN>" http://localhost:8000/api/v1/ingest/documents/{DOCUMENT_ID}
```
Vector index embeddings and SQLite chunk records are immediately dropped from the search index.
