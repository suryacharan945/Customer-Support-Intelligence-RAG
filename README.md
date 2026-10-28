# Multi-Context Intelligent RAG System: Self-Improving, Agentic Platform for Advanced Customer Support

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Storage: Google Drive First](https://img.shields.io/badge/Storage-Google%20Drive%205TB-4285F4.svg)](#storage-architecture)

An enterprise-grade, agentic Retrieval-Augmented Generation (RAG) platform leveraging **Multi-Context Prompting (MCP)** to retrieve, reason over, and synthesize technical support knowledge from disparate documentation sources (product manuals, troubleshooting guides, FAQs, and warranty agreements).

---

## 1. Project Directory Blueprint

```
Internship_RAG_MCP_Capstone/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI application factory & routes
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                      # Decoupled FastAPI dependency injection providers
│   │   ├── router.py                    # Aggregated API router
│   │   └── endpoints/
│   │       ├── health.py                # System health diagnostics & deep readiness probe
│   │       ├── rag.py                   # Baseline & Multi-Context RAG query endpoints
│   │       ├── documents.py             # Document upload, lifecycle management & deletion
│   │       ├── knowledge_base.py        # Knowledge base status & telemetry
│   │       ├── feedback.py              # Active learning human-in-the-loop feedback
│   │       └── analytics.py             # Performance telemetry & accuracy metrics
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic Settings with Google Drive defaults
│   │   └── logging.py                   # Structured console logging
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py                    # Multi-format document loader (pdf, txt, md)
│   │   ├── chunker.py                   # Recursive text splitter & deterministic chunker
│   │   ├── manifest.py                  # Deduplication engine & crash-safe manifest
│   │   └── cli.py                       # Standalone ingestion & preprocessing CLI
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── base.py                      # Abstract retriever interface
│   │   ├── category_selector.py         # Category-aware query routing engine
│   │   ├── bm25.py                      # BM25Okapi sparse keyword search engine
│   │   ├── embeddings.py                # Embedding provider abstraction (local, remote, mock)
│   │   ├── vector_store.py              # ChromaDB vector store adapter & category filtering
│   │   ├── chroma_backup.py             # Full ChromaDB persistence snapshot & restore manager
│   │   └── hybrid.py                    # Reciprocal Rank Fusion (RRF) dense + sparse engine
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── llm_client.py                # Decoupled LLM client (Colab, Cloud API, Mock)
│   │   ├── prompt_templates.py          # MCP synthesis & query expansion templates
│   │   ├── mcp_context.py               # Balanced multi-context assembly & injection defense
│   │   └── citation_validator.py        # Evidence citation validation & claim check
│   └── services/
│       ├── __init__.py
│       ├── ingestion_service.py         # Standalone ingestion & deduplication orchestrator
│       ├── rag_service.py               # End-to-end RAG orchestrator & query expansion
│       └── feedback_service.py          # Feedback collector & persistent archiver
├── frontend/
│   ├── __init__.py
│   ├── app.py                          # Streamlit application fallback & demonstration
│   ├── api_client.py                   # Decoupled HTTP API client with error boundaries
│   ├── state.py                        # Ephemeral session state manager
│   ├── components/
│   │   ├── badges.py                   # Lifecycle & provider visual status badges
│   │   ├── citations.py                # Grounded supporting citation cards
│   │   └── feedback_widget.py          # Active learning 1-5 star feedback form
│   └── views/
│       ├── chat_view.py                # Page A: Dual-mode RAG customer support chat
│       ├── documents_view.py           # Page B: Document lifecycle management & upload
│       ├── comparison_view.py          # Page C: Side-by-side Baseline vs MCP evaluation
│       ├── knowledge_base_view.py      # Page D: Telemetry, lifecycle & storage dashboard
│       └── about_view.py               # Page E: Architecture manual & diagnostics
├── web/                                 # Stage 10 Enterprise React Web Application (Vite + TS)
│   ├── src/
│   │   ├── App.tsx                     # React Router (7 routes) & Theme Provider
│   │   ├── api/                        # Typed API client & Pydantic-mirrored schemas
│   │   ├── components/                 # Primitives, AppShell, Chat, Docs & 3D Hero
│   │   ├── pages/                      # Dashboard, Chat, Documents, Compare, Analytics, Guide, Status
│   │   └── test/                       # Vitest component & application test suite
│   ├── package.json                    # Minimal npm dependencies (~294 MB node_modules)
│   └── vite.config.ts                  # Vite 6 dev server with /api proxy to FastAPI port 8000
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                       # Faithfulness, Context Relevance, Latency
│   ├── evaluator.py                     # Automated benchmark runner with Drive export
│   ├── retrieval_evaluator.py           # Retrieval benchmark engine (Recall@K, MRR, latency)
│   ├── retrieval_test_dataset.json      # Ground-truth test queries & relevance labels
│   ├── stage4_evaluator.py              # Dense vs Hybrid comparative benchmark
│   ├── stage7_evaluator.py              # Stage 7 Answer quality & safety benchmark runner
│   ├── stage7_evaluation_dataset.json   # 16 benchmark queries across 8 evaluation dimensions
│   ├── stage7b_live_results.json        # 32 live Mistral-7B generated responses & metrics
│   ├── stage8_comparison_results.json   # Audited comparative metrics & latency telemetry
│   └── held_out_dataset.json            # 10 strictly held-out test queries (anti-leakage)
├── notebooks/
│   ├── README.md                        # Remote compute workflow & GPU guidelines
│   ├── 01_colab_embedding_and_chroma_indexing.ipynb # Batch GPU embedding & index creation
│   └── 02_colab_mistral_rag_inference.ipynb         # 10-step Mistral-7B 4-bit NF4 inference server
├── scripts/
│   ├── verify_storage_and_sync.py       # Cloud mount validator & folder builder
│   ├── backup_to_drive.py               # Quiescent SQLite Online Backup & rotation
│   ├── test_backup_and_restore.py       # Sandboxed restoration test suite
│   ├── evaluate_retrieval.py            # Retrieval benchmark CLI runner
│   └── verify_ui_integration.py         # End-to-end FastAPI & Streamlit verification
├── tests/
│   ├── __init__.py
│   ├── test_health.py                   # FastAPI health & feedback tests (3 tests)
│   ├── test_rag_pipeline.py             # Agentic pipeline, providers & citations (14 tests)
│   ├── test_ingestion.py                # Loader, PDF extraction, boundary validation (10 tests)
│   ├── test_chunking.py                 # Recursive chunker, overlap & determinism (8 tests)
│   ├── test_duplicates.py               # Manifest persistence & duplicate skipping (4 tests)
│   ├── test_embeddings.py               # Dimensionality, normalization, provider errors (10 tests)
│   ├── test_vector_store.py             # Insertion, counts, category filter, top-k (10 tests)
│   ├── test_stage4_multi_context.py     # Stage 4 MCP, hybrid retrieval, citation checks (17 tests)
│   ├── test_stage5_api.py               # Stage 5 FastAPI endpoints, lifecycle, upload, delete (23 tests)
│   ├── test_stage6_ui.py                # Stage 6 Streamlit UI, API client, AppTest, components (22 tests)
│   ├── test_stage7_inference.py         # Stage 7 Remote LLM auth, token bounding, safety (10 tests)
│   ├── test_stage8_quality_audit.py     # Stage 8 Citation precision, latency, held-out test (8 tests)
│   └── test_retrieval.py                # Baseline retrieval, latency, snapshot restoration (7 tests)
├── docs/
│   ├── STAGE_8_IMPLEMENTATION_REPORT.md # Stage 8 quality audit & validation report
│   ├── STAGE_8_CITATION_AUDIT.md        # Citation taxonomy & 41.25% metric forensic audit
│   ├── STAGE_8_PERFORMANCE_ANALYSIS.md  # Latency deconstruction & sub-millisecond telemetry
│   ├── STAGE_8_EVALUATION_METHODOLOGY.md# Anti-leakage governance & synthetic KB limits
│   ├── STAGE_8_HUMAN_REVIEW_GUIDE.md    # 1-5 Likert rubrics & blank human scoring sheets
│   ├── STORAGE_CONFIGURATION_REPORT.md  # Detailed Stage 1B storage verification
│   ├── REQUIREMENTS_TRACEABILITY.md     # Traceability matrix to internship PDFs
│   ├── ARCHITECTURE.md                  # Comprehensive architectural design
│   ├── STAGE_1_IMPLEMENTATION_REPORT.md # Stage 1 completion summary
│   ├── STAGE_1C_CORRECTION_REPORT.md    # Stage 1C foundation corrections report
│   ├── STAGE_2_IMPLEMENTATION_REPORT.md # Stage 2 ingestion & preprocessing report
│   ├── STAGE_3_IMPLEMENTATION_REPORT.md # Stage 3 embedding & retrieval report
│   ├── STAGE_4_IMPLEMENTATION_REPORT.md # Stage 4 multi-context hybrid RAG report
│   ├── STAGE_5_IMPLEMENTATION_REPORT.md # Stage 5 FastAPI & document lifecycle report
│   ├── STAGE_6_IMPLEMENTATION_REPORT.md # Stage 6 Streamlit frontend & UI testing report
│   ├── STAGE_7_IMPLEMENTATION_REPORT.md # Stage 7 real inference & grounded evaluation report
│   ├── REAL_LLM_INFERENCE_GUIDE.md      # Operator runbook for Colab GPU Mistral-7B service
│   ├── ANSWER_QUALITY_EVALUATION.md     # Comparative answer quality, grounding & safety report
│   ├── END_TO_END_DEMO_REPORT.md        # Full multi-tier system demonstration & walkthrough
│   ├── STREAMLIT_USER_GUIDE.md          # Complete user manual for Streamlit dashboard
│   ├── UI_TEST_REPORT.md                # UI automated and manual verification report
│   ├── API_REFERENCE.md                 # Complete API reference and schemas
│   ├── END_TO_END_VERIFICATION.md       # Stage 5 end-to-end inquiry verification report
│   ├── EMBEDDING_AND_VECTOR_STORE.md    # Embedding models & collection specifications
│   └── CHROMADB_BACKUP_AND_RESTORE.md   # Persistence snapshot & restoration protocol
├── .gitignore                           # Cloud-safe exclusion rules
├── .env.example                         # Environment configuration template
├── README.md                            # Project documentation
└── pyproject.toml                       # Python packaging & tool configuration
```

---

## 2. Storage Architecture: Google Drive First

To operate smoothly under strict local disk constraints (< 1 GB budget):
- **Persistent Cloud Root**: `G:\My Drive\Internship_RAG_MCP_Capstone\` (via Google Drive for Desktop in **Stream files mode**).
  - Holds reference PDFs (`00_References/`), knowledge base documents (`03_Knowledge_Base/`), consistent ChromaDB database backups (`05_Vector_Database_Backups/`), and test evaluation logs (`06_Test_Results/`).
- **Minimal Local Workspace**: `C:\Users\surya\Internship_RAG_MCP_Capstone` (consumes **~0.15 MB**).
  - Houses active source code and local Git repository.
  - Active runtime ChromaDB database resides in `.chroma_live/` (excluded from cloud sync to avoid SQLite locking collisions).
- **Atomic Database Backup**: `python scripts/backup_to_drive.py` utilizes the **SQLite Online Backup API** (`sqlite3.Connection.backup()`) to merge live WAL pages into a clean, uncorrupted snapshot before uploading to Google Drive.

---

## 3. Remote Compute Decoupling (Google Colab)

Because the development machine uses integrated Intel Iris Xe Graphics and limited available RAM:
- **Embedding Generation & Chroma Indexing**: Computed on Google Colab's free **NVIDIA T4 GPU** via `notebooks/01_colab_embedding_and_chroma_indexing.ipynb`.
- **Mistral 7B Inference**: Served via Colab GPU via `notebooks/02_colab_mistral_rag_inference.ipynb` or remote high-speed API (Groq / Gemini).
- **Local Model Storage**: **0 GB**.

---

## 4. Quickstart & Verification

### Running the Complete Test Suite (148 Tests across 13 Suites)
```powershell
python -m pytest tests/ -v
```

### Running the Stage 7 Groundedness & Safety Evaluation Benchmark
```powershell
python evaluation/stage7_evaluator.py
```

### Running the Primary React Web Application (Port 5173)
```powershell
# In a terminal:
cd web
npm run dev
```
- Interactive React Application: `http://localhost:5173` (Proxies API calls to port 8000)

### Running the FastAPI Backend Server (Port 8000)
```powershell
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### Running the Streamlit Fallback Dashboard (Port 8501)
```powershell
streamlit run frontend/app.py --server.port 8501
```
- Streamlit Fallback: `http://localhost:8501`

### Executing Full UI Integration Verification & Screenshot Tool
```powershell
python scripts/verify_ui_integration.py
```

### Synchronizing Snapshots to Google Drive
```powershell
python scripts/backup_to_drive.py
```

### Validating Backup & Restore Integrity
```powershell
python scripts/test_backup_and_restore.py
```
