# REST API Reference — Customer Support Intelligence Platform

**Release Version:** `v1.0.0-rc1`  
**Base URL:** `http://localhost:8000/api/v1` (with root-level shortcuts enabled)  
**Interactive Documentation:** Swagger UI at `http://localhost:8000/docs`, ReDoc at `http://localhost:8000/redoc`  

---

## 1. System Health & Readiness

### `GET /api/v1/health` (or `/health`)
Returns comprehensive operational health diagnostics, uptime, storage capacity, and active compute models.

#### Response (HTTP 200 OK):
```json
{
  "status": "healthy",
  "app_name": "Multi-Context Intelligent RAG System",
  "version": "1.0.0-rc1",
  "environment": "development",
  "uptime_seconds": 754.2,
  "storage": {
    "google_drive_connected": false,
    "google_drive_root": "G:\\My Drive\\Internship_RAG_MCP_Capstone",
    "local_free_disk_gb": 56.83,
    "storage_budget_mb": 1024
  },
  "compute": {
    "llm_provider": "local",
    "model_name": "mistralai/Mistral-7B-Instruct-v0.3"
  }
}
```

---

## 2. RAG & Multi-Context Query Engine

### `POST /api/v1/rag/query` (or `/query`)
Executes an end-to-end grounded query with hybrid retrieval, query decomposition, universal evidence sufficiency gating, and citation validation.

#### Request Headers:
`Content-Type: application/json`

#### Request Body:
```json
{
  "query": "What is the standard print resolution of the ApexPrint ProX-400 and what is its maximum monthly duty cycle?",
  "session_id": "user-session-1234",
  "top_k": 5,
  "retrieval_mode": "multi_context",
  "llm_provider": "auto"
}
```

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | `string` | **Yes** | — | Customer support inquiry (min length: 1). |
| `session_id` | `string` | No | `"default-session"` | Session identifier for conversational memory. |
| `top_k` | `integer` | No | `5` | Number of context chunks retrieved per category (1-20). |
| `retrieval_mode` | `string` | No | `"multi_context"` | `"baseline"` (dense only) or `"multi_context"` (MCP hybrid). |
| `llm_provider` | `string` | No | `null` | `"auto"`, `"local"`, `"colab_remote"`, `"groq"`. |

#### Response (HTTP 200 OK):
```json
{
  "query": "What is the standard print resolution of the ApexPrint ProX-400 and what is its maximum monthly duty cycle?",
  "answer": "### 1. Executive Summary / Direct Answer\nSpecifications and Hardware Capabilities...",
  "retrieval_mode": "multi_context",
  "selected_categories": ["product_manual"],
  "evidence_status": "SUFFICIENT",
  "supporting_citations": [
    {
      "document_source": "apexprint_prox400_user_manual.md",
      "page_or_section": "1",
      "snippet": "Print Speed: Up to 45 pages per minute (ppm)... Resolution: Up to 1200 x 1200 dpi...",
      "relevance_score": 0.784,
      "category": "product_manual",
      "chunk_id": "doc_prod_de7386b29af7_c0001",
      "is_verified": true
    }
  ],
  "retrieval_latency_ms": 1054.1,
  "generation_latency_ms": 8.6,
  "execution_time_ms": 1062.7,
  "timing_breakdown": {
    "category_selection_ms": 12.1,
    "retrieval_dense_ms": 1040.2,
    "retrieval_sparse_ms": 0.5,
    "evidence_gate_ms": 0.6,
    "llm_generation_ms": 8.6,
    "citation_validation_ms": 2.1
  },
  "is_mock": false
}
```

---

## 3. Document Lifecycle Management

### `POST /api/v1/documents/upload`
Uploads and preprocesses a new document into the knowledge base.

#### Request Form-Data:
- `file`: Binary file stream (`.pdf`, `.txt`, `.md`). Max size: 10 MB.
- `category`: String (`general`, `engineering`, `architecture`, `evaluation`, `product_manual`, `troubleshooting`, `warranty`, `faq`).

#### Response (HTTP 201 Created):
```json
{
  "status": "SUCCESS",
  "document_id": "doc_engi_a3404c8bd668",
  "filename": "falcon_900_specs.md",
  "category": "engineering",
  "lifecycle_status": "pending_index",
  "is_searchable": false,
  "chunk_count": 2,
  "file_size_bytes": 1048,
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "message": "Document 'falcon_900_specs.md' successfully processed into 2 chunks."
}
```

### `POST /api/v1/documents/{document_id}/index`
Explicitly indexes a `pending_index` document into ChromaDB and BM25, transitioning it to `indexed` and setting `is_searchable = true`.

#### Response (HTTP 200 OK):
```json
{
  "document_id": "doc_engi_a3404c8bd668",
  "filename": "falcon_900_specs.md",
  "category": "engineering",
  "document_type": "md",
  "lifecycle_status": "indexed",
  "is_searchable": true,
  "chunk_count": 2,
  "file_size_bytes": 1048,
  "version": 1,
  "first_ingested": "2026-11-16T01:00:00",
  "last_seen": "2026-11-16T01:00:00"
}
```

### `GET /api/v1/documents`
Lists all active registered documents with filtering by category or lifecycle status.

### `DELETE /api/v1/documents/{document_id}`
Atomically removes document chunks from ChromaDB, BM25, and marks the manifest record as `deleted`. Safe and idempotent.

---

## 4. Human Feedback & Active Learning

### `POST /api/v1/feedback`
Records human feedback, ratings, and corrections for continuous improvement.

#### Request Body:
```json
{
  "query_id": "query_e2e_test_001",
  "rating": 5,
  "correction": null,
  "flagged_incorrect": false,
  "comment": "Accurate citations and verified technical specs."
}
```

#### Response (HTTP 200 OK):
```json
{
  "status": "success",
  "message": "Feedback recorded",
  "data": {
    "feedback_id": "fb_b819f727ce",
    "timestamp": "2026-11-16T01:00:00Z"
  }
}
```

---

## 5. HTTP Error Status Catalog

| Status Code | Error Condition | Detail Example |
|---|---|---|
| **400 Bad Request** | Path traversal attempt, invalid category, corrupted file header | `"Invalid filename: Path traversal sequences are strictly prohibited."` |
| **404 Not Found** | Document ID not found or already deleted | `"Document 'doc_123' not found or has been deleted."` |
| **413 Content Too Large** | Uploaded file exceeds 10 MB limit | `"File exceeds maximum upload size (10MB): 10486784 bytes"` |
| **422 Unprocessable** | Empty query text or whitespace only | `"Query text cannot be empty or whitespace only."` |
| **502 Bad Gateway** | Remote inference or vector database network failure | `"Remote LLM inference error: connection refused"` |
| **503 Unavailable** | Vector store uninitialized and mock mode disabled | `"Vector store unavailable: collection not initialized"` |
| **504 Gateway Timeout** | Remote inference call exceeded timeout ceiling | `"Remote LLM inference timeout after 30.0s"` |
