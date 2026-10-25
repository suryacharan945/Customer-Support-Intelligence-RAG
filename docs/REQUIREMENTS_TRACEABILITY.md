# Requirements Traceability Matrix (RTM)

**Project**: Multi-Context Intelligent RAG System: Self-Improving, Agentic Platform for Advanced Customer Support  
**Specification Source 1**: `Internship_Project_Specification.pdf`  
**Specification Source 2**: `Capstone_Project_Guide.pdf`  
**Target Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Date**: 2026-10-26  

---

## 1. Core Functional Requirements Traceability

| Req ID | Requirement Description (from Specs) | Implementing Module / File | Verification Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-01** | **Multi-Context RAG Engine**: Retrieve & combine product manuals, FAQs, troubleshooting guides, warranty docs; Top-K retrieval, context merging. | [`app/ingestion/loader.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/ingestion/loader.py), [`app/retrieval/vector_store.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/retrieval/vector_store.py), [`app/generation/mcp_context.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/generation/mcp_context.py) | Unit test / integration mock query | **IMPLEMENTED** |
| **REQ-02** | **Hybrid Retrieval System**: Fuse dense semantic embeddings with sparse keyword search (BM25 proxy). | [`app/retrieval/hybrid.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/retrieval/hybrid.py) | `HybridRetriever.retrieve()` weighted linear combination | **IMPLEMENTED** |
| **REQ-03** | **Agentic Decision Pipeline**: Multi-step query handling: Query -> Plan -> Retrieve -> Analyze -> Answer. | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py) | `RAGService.process_query()` flow | **IMPLEMENTED** |
| **REQ-04** | **Intelligent Query Rewriting**: Expansion, technical synonym injection, intent detection. | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L24-L31) | `_expand_query()` rule & intent expander | **IMPLEMENTED** |
| **REQ-05** | **Self-Improving Feedback Loop**: Human-in-the-loop rating (1–5 stars), text corrections, flagging. | [`app/api/endpoints/feedback.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/feedback.py), [`app/services/feedback_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/feedback_service.py) | `test_health.py::test_feedback_submission` | **IMPLEMENTED** |
| **REQ-06** | **Active Learning & Uncertainty Detection**: Detect low confidence answers and flag for user clarification. | [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L74-L77) | `requires_human_clarification` field | **IMPLEMENTED** |
| **REQ-07** | **Explainable AI (XAI) & Citations**: Source citations, section/page attribution, confidence scoring. | [`app/api/endpoints/rag.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/rag.py#L18-L23), [`app/services/rag_service.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/services/rag_service.py#L60-L72) | `test_health.py::test_rag_mock_query` | **IMPLEMENTED** |
| **REQ-08** | **RAG Evaluation Framework**: Faithfulness, context relevance, answer correctness metrics. | [`evaluation/metrics.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/metrics.py), [`evaluation/evaluator.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/evaluation/evaluator.py) | `RAGEvaluator.run_benchmark()` | **IMPLEMENTED** |
| **REQ-09** | **Real-Time REST API**: FastAPI application exposing `/rag/query`, `/feedback`, `/analytics/metrics`, `/health`. | [`app/main.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/main.py), [`app/api/router.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/router.py) | Interactive Swagger `/docs`, `test_health.py` | **IMPLEMENTED** |
| **REQ-10** | **Remote Compute Offloading**: Mistral-7B inference & heavy batch indexing offloaded to Google Colab GPU (0 GB local model storage). | [`notebooks/01_colab_embedding_and_chroma_indexing.ipynb`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/notebooks/01_colab_embedding_and_chroma_indexing.ipynb), [`notebooks/02_colab_mistral_rag_inference.ipynb`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/notebooks/02_colab_mistral_rag_inference.ipynb) | Google Colab test runs with Drive mount | **IMPLEMENTED** |
| **REQ-11** | **Google Drive Primary Storage**: Persistent data stored in `G:\My Drive\Internship_RAG_MCP_Capstone\` (Stream mode). | [`scripts/verify_storage_and_sync.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/scripts/verify_storage_and_sync.py), [`scripts/backup_to_drive.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/scripts/backup_to_drive.py) | SHA256 sync verification test & restoration test | **IMPLEMENTED** |

---

## 2. API Endpoint Traceability

| HTTP Method | Route | Description | Module Handler | Target Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | API Root Welcome & Service Links | [`app/main.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/main.py#L32) | 200 OK |
| `GET` | `/docs` | Interactive OpenAPI Swagger UI | FastAPI default | 200 OK |
| `GET` | `/api/v1/health` | Comprehensive System Health Diagnostics | [`app/api/endpoints/health.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/health.py#L14) | 200 OK |
| `POST` | `/api/v1/rag/query` | Multi-Context Retrieval & LLM Generation | [`app/api/endpoints/rag.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/rag.py#L35) | 200 OK |
| `POST` | `/api/v1/feedback/` | Human Feedback & Active Learning Logging | [`app/api/endpoints/feedback.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/feedback.py#L18) | 200 OK |
| `GET` | `/api/v1/analytics/metrics` | Operational Performance & Evaluation Telemetry | [`app/api/endpoints/analytics.py`](file:///C:/Users/surya/Internship_RAG_MCP_Capstone/app/api/endpoints/analytics.py#L9) | 200 OK |
