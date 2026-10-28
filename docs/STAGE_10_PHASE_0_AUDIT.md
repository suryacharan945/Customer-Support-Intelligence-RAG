# STAGE 10 — PHASE 0 REPOSITORY AUDIT AND BASELINE REPORT

**Project**: Multi-Context Intelligent RAG System — AI Customer Support Intelligence Platform  
**Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Git Branch**: `stage10-react-frontend` (Branched from `master` @ `801bf6e`)  
**Regression Baseline**: 148 passing tests (0 failures, 1 deprecation warning)  
**Execution Timestamp**: 2026-10-28T22:35:00+05:30  

---

## 1. Executive Summary & Audit Baseline

Prior to beginning frontend implementation for Stage 10, a comprehensive audit was executed across the repository structure, backend FastAPI routes, Pydantic schemas, Streamlit views, test suites, and evaluation artifacts.

### Baseline Verification Status
| Verification Check | Result | Evidence / Details |
| :--- | :--- | :--- |
| **Git Working Tree** | Clean | Switched to `stage10-react-frontend` |
| **Python Test Suite** | 148 / 148 PASS | `tests/test_*.py` verified in 38.37s |
| **Node.js Environment** | v22.15.0 | Modern LTS runtime supporting Vite, React 19/18, TypeScript |
| **NPM Package Manager**| 10.9.2 | Native Windows npm with package-lock capabilities |
| **Google Drive Backup** | Synchronized | `G:\My Drive\Internship_RAG_MCP_Capstone` synced |
| **Streamlit Fallback** | Preserved | Running concurrently on port 8501 (`frontend/app.py`) |
| **FastAPI Backend** | Online | Running on `http://127.0.0.1:8000` with CORS `allow_origins=["*"]` |

---

## 2. Existing Backend APIs Audit

The FastAPI backend exposes the following well-defined routes under prefix `/api/v1` and canonical aliases:

### 2.1 Diagnostics & Health
- `GET /health` & `GET /api/v1/health`: Basic uptime, storage connection, free disk GB.
- `GET /ready` & `GET /api/v1/ready`: Deep 5-subsystem readiness probe (Storage, Manifest, Vector Store, Embeddings, LLM Provider). Returns 200 OK or 503 Service Unavailable with checklist.

### 2.2 RAG & MCP Query Engine
- `POST /query` & `POST /api/v1/query`: Core RAG execution endpoint.
  - **Inputs**: `query` (str), `session_id` (str), `top_k` (int, 1-20), `retrieval_mode` (`"baseline"` | `"multi_context"`), `llm_provider` (`"auto"` | `"local"` | `"colab_remote"`).
  - **Outputs**: `QueryResponse` containing:
    - `answer` (str): Generated or synthesized response.
    - `retrieval_mode` (str): Mode used.
    - `selected_categories` (List[str]): Extracted topic categories.
    - `supporting_citations` (List[Citation]): Verified citations matching text claims.
    - `citations` (List[Citation]): All retrieved candidate chunks.
    - `evidence_status` (`"SUFFICIENT"` | `"PARTIAL"` | `"INSUFFICIENT"`).
    - `retrieval_latency_ms`, `generation_latency_ms`, `execution_time_ms`.
    - `timing_breakdown` (Dict): Sub-millisecond stage breakdown.
    - `provider_status` (`"ONLINE_COLAB_GPU"`, `"LOCAL_GROUNDED_SYNTHESIS"`, `"LOCAL_GROUNDED_FALLBACK"`, `"READY_FOR_COLAB_INFERENCE"`).
    - `citation_precision` (float): Ratio of verified asserted citations to total asserted.
    - `context_utilization` (float): Ratio of cited chunks to candidate chunks.

### 2.3 Document Lifecycle Management
- `POST /documents` & `POST /api/v1/documents`: Multipart document upload (`.pdf`, `.txt`, `.md`). Maximum 10MB limit. Idempotent hash check.
- `GET /documents` & `GET /api/v1/documents`: List documents filtered by category or status (`uploaded`, `processed`, `pending_index`, `indexed`, `indexing_failed`, `deleted`).
- `GET /documents/{document_id}` & `GET /api/v1/documents/{document_id}`: Single document details.
- `DELETE /documents/{document_id}` & `GET /api/v1/documents/{document_id}`: Atomic cross-layer deletion (Vector store, BM25, physical disk, manifest).

### 2.4 Knowledge Base Telemetry
- `GET /knowledge-base/status` & `GET /api/v1/knowledge-base/status`: Active documents count, active chunks, category breakdown, lifecycle status counts, ChromaDB collection metrics, Google Drive sync status.

### 2.5 Active Learning & Feedback
- `POST /feedback` & `POST /api/v1/feedback`: Submit user feedback with 1-5 star rating, qualitative comments, incorrect flags, and human corrections.

### 2.6 Analytics & Frozen Benchmarks
- `GET /analytics/metrics` & `GET /api/v1/analytics/metrics`: Operational metrics.
- `GET /analytics/evaluation-summary` & `GET /api/v1/analytics/evaluation-summary`: Frozen Stage 8 comparative results, Stage 8B held-out validation data, citation metrics, and explicit limitations.

---

## 3. Existing Streamlit Features to Replicate in React

| Streamlit View | Existing Capabilities & Features | React Stage 10 Target Page |
| :--- | :--- | :--- |
| **Global Shell** | Sidebar navigation, backend health badge, Drive sync indicator, Clear chat action | Global App Shell, Header, Sidebar, Status Indicators |
| **Chat View** | Prompt input (Enter to submit), example prompts, baseline vs MCP radio, Top-K slider, category focus filter, LLM provider selector, citation inspection cards, feedback widget | **AI Support Chat** (`/chat`) |
| **Documents View** | Drag & drop upload, file size / format validation, category selector, lifecycle badge table, delete button with confirmation | **Knowledge Base Studio** (`/documents`) |
| **Comparison View** | Side-by-side Mode A vs Mode B query execution, dual citation inspection, comparative latency delta metrics | **Baseline vs MCP Comparison** (`/comparison`) |
| **Knowledge Base View** | Category distribution cards, lifecycle breakdown, storage telemetry | **Dashboard** (`/`) & **Knowledge Base Studio** |
| **About View** | Multi-Context RAG explanation, architecture overview, citations methodology | **How It Works** (`/how-it-works`) & **Dashboard** |
| *New in Stage 10* | Evaluation charts, P95 latency distributions, held-out vs development benchmarks | **Evaluation & Analytics** (`/analytics`) |
| *New in Stage 10* | Comprehensive subsystem health matrix, provider toggle, error diagnosis | **System Status** (`/status`) |

---

## 4. Architectural Rules & Technical Constraints

1. **Zero Model Weight Downloads**: Keep all local execution lightweight. No multi-gigabyte PyTorch checkpoints on Windows.
2. **Preserve Pydantic Schema Fidelity**: React TypeScript models must map 1:1 to `QueryResponse`, `Citation`, `DocumentSummary`, `KnowledgeBaseStatusResponse`.
3. **No Fabricated Confidence or Streaming**: Do not simulate pseudo-streaming or fabricate uncalibrated confidence percentages.
4. **Security & Secrets**: Never store Colab tokens or backend API keys in browser storage or client bundles. All LLM calls proxy via FastAPI.
5. **Streamlit Fallback**: The existing Streamlit app (`frontend/app.py`) remains completely functional on port 8501 throughout Stage 10.
