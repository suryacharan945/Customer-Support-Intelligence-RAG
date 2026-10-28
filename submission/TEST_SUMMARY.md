# Automated Test Summary & Regression Baseline

**Project**: Customer Support Intelligence Assistant (RAG + Multi-Contextual Prompting)  
**Execution Environment**: Python 3.13.9 | Windows 11 64-bit  
**Framework**: `pytest 9.1.1` (with `anyio`, `asyncio`)  
**Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Execution Timestamp**: 2026-10-28 18:44:12 IST  
**Outcome**: **148 PASSED / 0 FAILED / 0 SKIPPED (100% Passing)** in 66.65s  

---

## 1. Test Suite Distribution & Coverage

| Test Module / Suite | Test Count | Target Subsystem / Functional Scope | Status |
| :--- | :---: | :--- | :---: |
| `tests/test_chroma_backup.py` | 2 | Tarball snapshot creation, Drive synchronization, restoration integrity | **PASS** |
| `tests/test_chunking.py` | 8 | Header-aware chunking, token boundary enforcement, overlap consistency | **PASS** |
| `tests/test_duplicates.py` | 4 | SHA-256 content hashing, duplicate detection, manifest tracking | **PASS** |
| `tests/test_embeddings.py` | 10 | MiniLM embedder, vector normalization, dimensionality verification | **PASS** |
| `tests/test_health.py` | 3 | Health endpoints, storage telemetry, feedback submission | **PASS** |
| `tests/test_ingestion.py` | 10 | Multi-format loading (.md, .txt, .pdf), manifest persistence, categories | **PASS** |
| `tests/test_rag_pipeline.py` | 14 | Query expansion, planning, empty retrieval handling, citation mapping | **PASS** |
| `tests/test_retrieval.py` | 7 | Vector store retrieval, top-$k$ filtering, cosine distance ordering | **PASS** |
| `tests/test_stage4_multi_context.py`| 17 | CategorySelector, BM25Okapi, RRF ($k=60$), MCPContextBuilder, injection defense | **PASS** |
| `tests/test_stage5_api.py` | 23 | Dependency injection, 6 lifecycle states, atomic deletion, deep readiness | **PASS** |
| `tests/test_stage6_ui.py` | 22 | APIClient, Streamlit views, session state, lifecycle searchability invariants | **PASS** |
| `tests/test_stage7_inference.py` | 10 | Remote LLMClient, Bearer authentication, timeout enforcement, conflict detection | **PASS** |
| `tests/test_stage8_quality_audit.py`| 8 | True Citation Precision, Context Chunk Utilization, timing breakdowns, held-out separation | **PASS** |
| `tests/test_vector_store.py` | 10 | ChromaDB collection management, upserts, distance metrics, query filters | **PASS** |
| **TOTAL** | **148** | **Complete Full-Stack Application & Evaluation Stack** | **100% PASS** |

---

## 2. Key Verified Invariants

1. **Strict Searchability Invariant (`test_stage5_api.py`, `test_stage6_ui.py`)**:
   - Documents in states `uploaded`, `processed`, or `pending_index` have `is_searchable = False`.
   - The retrieval pipeline guarantees that unindexed documents are never returned as evidence to the LLM.

2. **Atomic Document Deletion Invariant (`test_stage5_api.py`)**:
   - Invoking `DELETE /api/v1/documents/{id}` purges raw disk files, dense vector chunks from ChromaDB, and sparse BM25 indices simultaneously.
   - Subsequent retrieval calls return zero chunks from the deleted document; duplicate deletion returns HTTP 404.

3. **Decoupled API Client Invariant (`test_stage6_ui.py`)**:
   - The UI layer (`frontend/`) contains zero direct database or vector store imports.
   - All operations are mediated by `frontend/api_client.py` using typed HTTP exceptions (`APIConnectionError`, `APITimeoutError`, `APIStatusError`).

4. **Citation Precision Decoupling Invariant (`test_stage8_quality_audit.py`)**:
   - $P_{\text{true}} = |V_{\text{app}}| / |A_{\text{model}}|$ strictly isolates model-asserted citations from candidate pool size.
   - Confirms that high candidate counts do not mathematically artificially depress true precision.
