# Deployment & Operations Guide — Customer Support Intelligence Platform

**Release Version:** `v1.0.0-rc1`  
**Classification:** Release Candidate / Controlled Pilot Ready  
**Date:** 2026-11-16  

---

## 1. System Requirements & Prerequisites

### 1.1 Compute & Hardware Specifications
- **Operating System:** Windows 10/11, macOS 12+, or Ubuntu Linux 20.04+ LTS.
- **Python Runtime:** Python 3.10, 3.11, 3.12, or 3.13.
- **Node.js Runtime:** Node.js 18.x or 20.x+ (with npm 9+).
- **RAM:** Minimum 8 GB (16 GB recommended for local embedding inference).
- **Disk Space:** Minimum 5 GB free disk space (local project footprint is < 20 MB).
- **GPU:** Optional. CPU inference for `all-MiniLM-L6-v2` embeddings is fully optimized.

---

## 2. Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

### 2.1 Configuration Key Reference

| Variable Name | Default Value | Description |
|---|---|---|
| `ENVIRONMENT` | `development` | Runtime environment mode (`development`, `staging`, `production`). |
| `APP_HOST` | `0.0.0.0` | Host IP for FastAPI ASGI server. |
| `APP_PORT` | `8000` | Port for FastAPI server. |
| `API_V1_PREFIX` | `/api/v1` | URL prefix for REST endpoints. |
| `GOOGLE_DRIVE_ROOT` | `G:\My Drive\Internship_RAG_MCP_Capstone` | Persistent storage root for dataset backups and ChromaDB snapshots. |
| `LOCAL_EPHEMERAL_CHROMA_DIR` | `.chroma_live` | Local ephemeral cache directory for ChromaDB vector indices. |
| `LOCAL_MAX_STORAGE_BUDGET_MB` | `1024` | Local disk storage limit (enforces cleanup if exceeded). |
| `LLM_PROVIDER` | `colab_remote` | Synthesis provider: `colab_remote`, `local`, `groq`, `gemini`, `ollama`. |
| `ALLOW_LOCAL_FALLBACK` | `true` | Allows local grounded synthesis if remote LLM endpoint is offline. |
| `ALLOW_MOCK_FALLBACK` | `false` | **CRITICAL:** Set to `false` to ensure real grounded retrieval and prevent silent test mock data leaks. |
| `EMBEDDING_MODEL_NAME` | `sentence-transformers/all-MiniLM-L6-v2` | SentenceTransformer embedding model identifier. |
| `TOP_K_RETRIEVAL` | `5` | Maximum number of candidate chunks returned per query channel. |
| `HYBRID_SEARCH_ALPHA` | `0.6` | Weight for dense vector search (0.6 dense + 0.4 sparse BM25). |
| `BM25_ENABLED` | `true` | Enables in-memory BM25Okapi sparse keyword index. |

---

## 3. Starting the Services

### 3.1 Backend Service (FastAPI)

#### Development Mode:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Production Mode (Multiple Workers):
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Verify backend health:
```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "app_name": "Multi-Context Intelligent RAG System",
  "version": "1.0.0-rc1",
  "environment": "development",
  "storage": {
    "google_drive_connected": false,
    "local_free_disk_gb": 56.8,
    "storage_budget_mb": 1024
  },
  "compute": {
    "llm_provider": "local",
    "model_name": "mistralai/Mistral-7B-Instruct-v0.3"
  }
}
```

### 3.2 Frontend Service (React + Vite)

#### Development Mode:
```bash
cd web
npm install
npm run dev
```
Access UI at `http://localhost:5173/`.

#### Production Build & Static Serving:
```bash
cd web
npm run build
npm run preview -- --port 5173 --host 0.0.0.0
```
Or serve `web/dist` using Nginx, Caddy, or any static HTTP web server.

---

## 4. Backup & Disaster Recovery Runbook

### 4.1 Automated Google Drive & Local Backup
The platform implements a crash-safe backup procedure that archives:
1. Source code and scripts (`source_backup_<timestamp>.zip`)
2. Ingestion manifest and vector database (`chroma_snapshot_<timestamp>.zip`)
3. SQLite database integrity verification

Run backup:
```bash
python scripts/backup_to_drive.py
```

### 4.2 Restoring from Backup Snapshot
To restore a corrupted or deleted vector index from snapshot:
```bash
python scripts/test_backup_and_restore.py
```
This script validates snapshot extraction, integrity hashes, and confirms that the vector index resumes query answering without re-indexing.

---

## 5. Security & Boundary Hardening Checklist

- [x] **Path Traversal Defense:** Filenames containing `../`, `/`, or `\` are sanitized or rejected with HTTP 400.
- [x] **File Size Gate:** Files exceeding 10 MB are rejected with HTTP 413.
- [x] **Content Validation:** PDFs verified for `%PDF-` magic header; text files checked for valid UTF-8.
- [x] **Searchability Gating:** Uploaded files enter `pending_index` and are never searchable until explicitly indexed.
- [x] **Secrets & Key Safety:** Zero API keys or credentials stored in repository source code or client bundles.
- [x] **Mock Isolation:** `ALLOW_MOCK_FALLBACK` is strictly `False`.
