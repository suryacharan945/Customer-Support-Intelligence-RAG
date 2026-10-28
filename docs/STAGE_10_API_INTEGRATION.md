# Stage 10 — API Integration & Service Layer Specification
**Project**: Multi-Context Intelligent RAG System — Customer Support Intelligence Platform  
**Document**: STAGE_10_API_INTEGRATION.md  
**Version**: 1.0.0  
**Date**: October 2026  
**Status**: APPROVED & VERIFIED  

---

## 1. Overview & Connection Architecture

The React web application integrates with the FastAPI backend through a typed API client (`web/src/api/client.ts`). The client leverages standard HTTP fetch APIs coupled with `AbortController` timeouts and strict TypeScript schemas matching the backend Pydantic models.

- **Development Base URL**: `/api/v1` (Proxied via Vite dev server at `http://127.0.0.1:5173` to `http://127.0.0.1:8000`)
- **Production Base URL**: Configurable via `VITE_API_BASE_URL` environment variable.

---

## 2. Integrated API Endpoints

### 2.1 Diagnostics & Subsystem Probes
- `GET /api/v1/health`:
  - **Purpose**: High-level health check, storage budget telemetry, and active LLM configuration.
  - **Timeout**: 4,000 ms.
  - **Response Model**: `SystemHealthResponse`.
- `GET /api/v1/ready`:
  - **Purpose**: Deep readiness probe verifying 5 core subsystems: `storage`, `manifest`, `vector_store`, `embedding_provider`, and `llm_provider`.
  - **Timeout**: 5,000 ms.
  - **Response Model**: `SystemReadyResponse`.

### 2.2 RAG & Multi-Context Prompting Query Engine
- `POST /api/v1/query`:
  - **Purpose**: Execute customer support queries under either `baseline` (dense vector search) or `multi_context` (multi-category query decomposition and hybrid retrieval).
  - **Timeout**: 60,000 ms (accommodates remote inference latency).
  - **Request Body**:
    ```json
    {
      "query": "What is the standard warranty period for the ApexPrint ProX-400?",
      "retrieval_mode": "multi_context",
      "top_k": 5,
      "session_id": "session_abc123",
      "llm_provider": "auto"
    }
    ```
  - **Response Model**: `QueryResponse` (includes `answer`, `supporting_citations`, `retrieval_latency_ms`, `selected_categories`, and timing breakdowns).

### 2.3 Knowledge Base & Document Management
- `GET /api/v1/knowledge-base/status`:
  - **Purpose**: Retrieve vector store metrics, indexed chunk counts, and category breakdowns.
  - **Response Model**: `KnowledgeBaseStatusResponse`.
- `GET /api/v1/documents`:
  - **Purpose**: Retrieve all registered documents in the ingestion manifest, with optional `category` or `status` filtering.
  - **Response Model**: `DocumentListResponse`.
- `POST /api/v1/documents/upload`:
  - **Purpose**: Upload a new text or markdown document into the knowledge base, triggering automatic chunking, embedding, and indexing.
  - **Request**: `multipart/form-data` containing `file` and `category`.
  - **Response Model**: `DocumentUploadResponse`.
- `DELETE /api/v1/documents/{document_id}`:
  - **Purpose**: Soft delete a document from the manifest and remove its chunks from the Chroma vector collection.
  - **Response Model**: `DocumentDeleteResponse`.

### 2.4 User Feedback Loop
- `POST /api/v1/feedback`:
  - **Purpose**: Submit user quality ratings (1-5 stars), optional corrections, and hallucination flags.
  - **Response Model**: `FeedbackSubmissionResponse`.

### 2.5 Analytics & Benchmark Telemetry
- `GET /api/v1/analytics/evaluation-summary`:
  - **Purpose**: Retrieve frozen Stage 8 comparative benchmark and Stage 8B held-out validation dataset results.
  - **Response Model**: `EvaluationSummaryResponse`.

---

## 3. Error Handling & Timeout Strategy

1. **Structured Error Hierarchy**: All non-2xx responses are mapped to `ApiClientError` containing the HTTP status code, endpoint, and server error details.
2. **Timeout Protection**: Network calls enforce strict timeouts via `AbortSignal.timeout` or `AbortController` to prevent hanging UI spinners during network blips.
3. **User-Friendly Error Banners**: Errors are surfaced via dismissible toast notifications or contextual inline banners with retry actions.
