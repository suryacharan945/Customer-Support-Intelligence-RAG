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
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py                       # Faithfulness, Context Relevance, Latency
│   ├── evaluator.py                     # Automated benchmark runner with Drive export
│   ├── retrieval_evaluator.py           # Retrieval benchmark engine (Recall@K, MRR, latency)
│   └── retrieval_test_dataset.json      # Ground-truth test queries & relevance labels
├── notebooks/
│   ├── README.md                        # Remote compute workflow & GPU guidelines
│   ├── 01_colab_embedding_and_chroma_indexing.ipynb # Batch GPU embedding & index creation
│   └── 02_colab_mistral_rag_inference.ipynb         # Mistral-7B inference server
├── scripts/
│   ├── verify_storage_and_sync.py       # Cloud mount validator & folder builder
│   ├── backup_to_drive.py               # Quiescent SQLite Online Backup & rotation
│   ├── test_backup_and_restore.py       # Sandboxed restoration test suite
│   └── evaluate_retrieval.py            # Retrieval benchmark CLI runner
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
│   └── test_retrieval.py                # Baseline retrieval, latency, snapshot restoration (7 tests)
├── docs/
│   ├── STORAGE_CONFIGURATION_REPORT.md  # Detailed Stage 1B storage verification
│   ├── REQUIREMENTS_TRACEABILITY.md     # Traceability matrix to internship PDFs
│   ├── ARCHITECTURE.md                  # Comprehensive architectural design
│   ├── STAGE_1_IMPLEMENTATION_REPORT.md # Stage 1 completion summary
│   ├── STAGE_1C_CORRECTION_REPORT.md    # Stage 1C foundation corrections report
│   ├── STAGE_2_IMPLEMENTATION_REPORT.md # Stage 2 ingestion & preprocessing report
│   ├── STAGE_3_IMPLEMENTATION_REPORT.md # Stage 3 embedding & retrieval report
│   ├── STAGE_4_IMPLEMENTATION_REPORT.md # Stage 4 multi-context hybrid RAG report
│   ├── STAGE_5_IMPLEMENTATION_REPORT.md # Stage 5 FastAPI & document lifecycle report
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

### Running the Complete Test Suite (108 Tests)
```powershell
python -m pytest tests/ -v
```

### Knowledge Base Ingestion CLI
Run the standalone ingestion CLI to process new documents or re-index the synthetic knowledge base on Google Drive:
```powershell
# Ingest entire Google Drive knowledge base
python app/ingestion/cli.py "G:\My Drive\Internship_RAG_MCP_Capstone\03_Knowledge_Base"

# Force re-indexing of modified/duplicate documents
python app/ingestion/cli.py "G:\My Drive\Internship_RAG_MCP_Capstone\03_Knowledge_Base" --force

# Ingest a single document with explicit category
python app/ingestion/cli.py "path/to/manual.pdf" --category product_manual
```

### Retrieval Evaluation Benchmark CLI
```powershell
# Run benchmark with mock embedding provider and export to Google Drive
python scripts/evaluate_retrieval.py --mock --export

# Run benchmark with category-filtered retrieval
python scripts/evaluate_retrieval.py --mock --category-filter
```

### Running the FastAPI Server Locally
```powershell
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/api/v1/health`

### Synchronizing Snapshots to Google Drive
```powershell
python scripts/backup_to_drive.py
```

### Validating Backup & Restore Integrity
```powershell
python scripts/test_backup_and_restore.py
```
