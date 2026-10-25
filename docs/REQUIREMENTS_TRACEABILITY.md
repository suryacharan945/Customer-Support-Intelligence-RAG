# Requirements Traceability Matrix (RTM)

**Project**: Multi-Context Intelligent RAG System: Self-Improving, Agentic Platform for Advanced Customer Support  
**Specification Source 1**: `Internship_Project_Specification.pdf`  
**Specification Source 2**: `Capstone_Project_Guide.pdf`  
**Target Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Last Updated**: 2026-10-26 (Post-Stage 2 Implementation)  

---

## 1. Core Functional Requirements Traceability

| Req ID | Requirement Description | Implementing Module / File | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | **Multi-Context Ingestion & Preprocessing**: Ingest PDF, TXT, Markdown across 4 categories (`product_manual`, `troubleshooting`, `warranty`, `faq`); page extraction, deterministic chunking, duplicate manifest management. | [`app/ingestion/loader.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/ingestion/loader.py), [`app/ingestion/chunker.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/ingestion/chunker.py), [`app/ingestion/manifest.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/ingestion/manifest.py), [`app/services/ingestion_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/ingestion_service.py), [`app/ingestion/cli.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/ingestion/cli.py) | `tests/test_ingestion.py` (10 tests), `tests/test_chunking.py` (8 tests), `tests/test_duplicates.py` (4 tests) | **VERIFIED (STAGE 2)** |
| **REQ-02** | **Hybrid Retrieval System**: Fuse dense semantic embeddings with sparse keyword search (BM25 proxy). | [`app/retrieval/hybrid.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/retrieval/hybrid.py) | Weighted score fusion verified in pipeline unit tests | **VERIFIED (STAGE 1C)** |
| **REQ-03** | **Agentic Decision Pipeline**: Query -> Plan -> Retrieve -> Analyze -> Answer; explicit error propagation instead of silent mock fallbacks. | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py) | `tests/test_rag_pipeline.py::test_empty_retrieval_returns_evidence_insufficient_response` | **VERIFIED (STAGE 1C)** |
| **REQ-04** | **Intelligent Query Rewriting**: Expansion, technical synonym injection, intent detection. | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L32-L39) | `_expand_query()` verified in pipeline tests | **VERIFIED (STAGE 1C)** |
| **REQ-05** | **Self-Improving Feedback Loop**: Human-in-the-loop rating (1–5 stars), text corrections, flagging. | [`app/api/endpoints/feedback.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/feedback.py), [`app/services/feedback_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/feedback_service.py) | `tests/test_health.py::test_feedback_submission` | **VERIFIED (STAGE 1C)** |
| **REQ-06** | **Active Learning & Uncertainty Handling**: Flag queries with zero or weak evidence (`evidence_found=False`, `requires_human_clarification=True`). | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L60-L77) | `tests/test_rag_pipeline.py::test_empty_retrieval_returns_evidence_insufficient_response` | **VERIFIED (STAGE 1C)** |
| **REQ-07** | **Conservative Citations & XAI**: Source citations strictly restricted to retrieved passages; uncalibrated similarity isolated from correctness probability. | [`app/api/endpoints/rag.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/rag.py#L20-L40), [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L90-L105) | `tests/test_rag_pipeline.py::test_conservative_citations_match_retrieved_evidence` | **VERIFIED (STAGE 1C)** |
| **REQ-08** | **RAG Evaluation Framework**: Faithfulness, context relevance, answer correctness metrics. | [`evaluation/metrics.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/metrics.py), [`evaluation/evaluator.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/evaluator.py) | `RAGEvaluator.run_benchmark()` | **SCAFFOLDED** |
| **REQ-09** | **Real-Time REST API**: FastAPI application exposing `/rag/query`, `/feedback`, `/analytics/metrics`, `/health`. | [`app/main.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/main.py), [`app/api/router.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/router.py) | `tests/test_health.py`, `tests/test_rag_pipeline.py` | **VERIFIED (STAGE 1C)** |
| **REQ-10** | **Remote Compute Decoupling**: Mistral-7B inference & heavy batch indexing offloaded to Google Colab GPU (0 GB local model storage). | [`notebooks/01_colab_embedding_and_chroma_indexing.ipynb`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/notebooks/01_colab_embedding_and_chroma_indexing.ipynb), [`notebooks/02_colab_mistral_rag_inference.ipynb`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/notebooks/02_colab_mistral_rag_inference.ipynb) | Architecture verified; zero local weights downloaded | **VERIFIED (STAGE 1C)** |
| **REQ-11** | **Google Drive Primary Storage**: Persistent data stored in `G:\My Drive\Internship_RAG_MCP_Capstone\` (Stream mode). | [`scripts/verify_storage_and_sync.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/scripts/verify_storage_and_sync.py), [`scripts/backup_to_drive.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/scripts/backup_to_drive.py) | Tested via SQLite Online Backup API restoration test & SHA256 sync verification | **VERIFIED (STAGE 1C)** |

---

## 2. API Endpoint Traceability & Status Codes

| HTTP Method | Route | Description | Module Handler | Verified Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root Welcome & Service Links | [`app/main.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/main.py#L32) | 200 OK |
| `GET` | `/docs` | Interactive OpenAPI Swagger UI | FastAPI default | 200 OK |
| `GET` | `/api/v1/health` | Comprehensive System Health Diagnostics | [`app/api/endpoints/health.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/health.py#L14) | 200 OK |
| `POST` | `/api/v1/rag/query` | Multi-Context Retrieval & LLM Generation | [`app/api/endpoints/rag.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/rag.py#L43) | 200 OK / 503 / 502 / 504 / 501 / 500 |
| `POST` | `/api/v1/feedback/` | Human Feedback & Active Learning Logging | [`app/api/endpoints/feedback.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/feedback.py#L18) | 200 OK |
| `GET` | `/api/v1/analytics/metrics` | Operational Performance & Evaluation Telemetry | [`app/api/endpoints/analytics.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/analytics.py#L9) | 200 OK |
