# ApexPrint Customer Support Intelligence Assistant — Streamlit User Guide

## 1. Introduction

The **ApexPrint Customer Support Intelligence Assistant** web application provides an enterprise-ready dashboard for support agents, technical evaluators, and system administrators. It interfaces with the FastAPI backend to deliver:

- Dual-mode RAG question answering (**Baseline** vs **Multi-Context Hybrid**)
- Grounded citations directly linked to authoritative ApexPrint documentation
- Document lifecycle ingestion across 6 stages
- Real-time operational telemetry and cloud synchronization metrics
- Active learning feedback submission

---

## 2. Quickstart & Installation

### Prerequisites
- Python 3.11+ (Windows or Linux)
- FastAPI backend installed in project repository
- Google Drive for Desktop mounted at `G:\My Drive` (recommended)

### Launching the Application

1. **Start the FastAPI Backend Service**:
   ```bash
   cd C:\Users\surya\Internship_RAG_MCP_Capstone
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

2. **Start the Streamlit Frontend Dashboard**:
   ```bash
   cd C:\Users\surya\Internship_RAG_MCP_Capstone
   streamlit run frontend/app.py --server.port 8501
   ```

3. **Access the Interface**:
   Open your browser and navigate to:
   [http://localhost:8501](http://localhost:8501)

### Configuration Options
- **Backend URL**: Set via environment variable `FASTAPI_BASE_URL` (default: `http://127.0.0.1:8000`), or customize live in the Streamlit sidebar under **⚙️ Connection Settings**.

---

## 3. User Interface Guide

### 3.1 Sidebar & System Status

The left sidebar provides persistent status telemetry and global controls:
- **🟢 Backend Online / 🔴 Backend Offline**: Displays instantaneous connectivity to FastAPI, system uptime, and local free disk space.
- **Navigation Menu**: Switch between all 5 dashboard views.
- **🧹 Clear Conversation**: Resets ephemeral chat turns and feedback records.
- **⚙️ Connection Settings**: Update the target FastAPI base URL dynamically.

---

### 3.2 Page A: Customer Support Chat Assistant

The primary conversational interface for customer inquiry resolution.

#### How to Use:
1. **Configure Retrieval Parameters** (Optional):
   - Click **⚙️ Retrieval & Prompting Configuration**.
   - Select **Multi-Context (MCP Hybrid)** (default) for complex inquiries requiring cross-category evidence, or **Baseline (Dense Only)** for single-channel semantic search.
   - Select a **Category Focus** if you wish to constrain retrieval, or leave on **All Categories (Auto-Detect)**.
   - Adjust the **Top-K Chunks** slider (1 to 10).
2. **Submit an Inquiry**:
   - Type your question in the bottom chat bar, or click one of the quick example prompt buttons (`📌 Q1` through `📌 Q4`).
3. **Inspect the Grounded Answer**:
   - The assistant emits a response synthesized strictly from retrieved passages.
   - Review metadata: retrieval mode badge, selected categories, provider status, and retrieval latency.
4. **Verify Citations**:
   - Expand the **📚 Sources & Citations** accordion.
   - Inspect verified supporting excerpts with exact document filenames, page numbers, relevance percentages, and chunk IDs.
5. **Submit Agent Feedback**:
   - Under the response, expand **⭐ Rate & Provide Feedback**.
   - Rate the quality from 1 to 5 stars, check the hallucination flag if facts are unsupported, and click **Submit Feedback**.

---

### 3.3 Page B: Document Lifecycle Management

Enables documentation teams to ingest manuals, policies, and troubleshooting guides.

#### Tab 1: Ingested Knowledge Base
- **Filter**: Filter documents by category (`product_manual`, `troubleshooting`, `warranty`, `faq`) or lifecycle state.
- **Lifecycle Badges**:
  - `✅ Indexed & Searchable`: Vector embeddings upserted to ChromaDB; actively queried by RAG.
  - `⏳ Pending Indexing (Not Searchable)`: Processed and chunked; awaiting vector indexing.
  - `⚙️ Processed (Not Searchable)`: File loaded and chunked.
  - `📥 Uploaded (Not Searchable)`: Staged file received.
  - `❌ Indexing Failed`: Vector store insertion failed.
  - `🗑️ Deleted`: Marked deleted; purged from vector indices.
- **Atomic Deletion**:
  - Check the confirmation box: `Confirm permanent deletion of [filename]`.
  - Click `🗑️ Delete` to permanently remove the source file, clear ChromaDB vectors, and remove BM25 tokens.

#### Tab 2: Ingest New Document
1. Select a file (`.pdf`, `.txt`, `.md`) up to 10 MB.
2. Choose the appropriate target category.
3. Click **🚀 Process & Ingest Document**.
4. The system validates the file signature, generates semantic chunks, updates the ingestion manifest, and marks the document as `pending_index`.

---

### 3.4 Page C: Baseline vs Multi-Context Comparison

Directly compares the two RAG strategies side by side for evaluation.

#### How to Use:
1. Enter a support question or select one of the sample comparison prompts.
2. Click **🚀 Run Comparative Analysis**.
3. Inspect side-by-side columns:
   - **Mode A (Baseline)**: Dense semantic search across the entire corpus.
   - **Mode B (Multi-Context)**: Intent category routing + hybrid (Dense + BM25) search with Reciprocal Rank Fusion.
4. Review comparative metrics table: latency difference, category coverage, and verified citation counts.

---

### 3.5 Page D: Knowledge Base Status & Diagnostics

Provides enterprise observability over corpus health and backend readiness.

#### Monitored Metrics:
- **Core Corpus Metrics**: Active documents, searchable documents, chunk count, ChromaDB vector count.
- **Lifecycle State Machine**: Instantaneous counts across all 6 states (`uploaded`, `processed`, `pending_index`, `indexed`, `indexing_failed`, `deleted`).
- **Category Coverage**: Document count and percentage distribution by category.
- **Subsystem Readiness**: Deep readiness probes checking storage, manifest, vector store, embedding provider, and LLM configuration.
- **Storage Telemetry**: Google Drive persistent mount path, local free disk space, and local storage budget.

---

### 3.6 Page E: System Architecture & Engineering Principles

A detailed reference manual embedded in the dashboard explaining:
- End-to-end RAG workflow.
- Multi-Contextual Prompting intent analysis and prompt balancing.
- Reciprocal Rank Fusion ($k=60$) mathematics.
- Citation groundedness validation rules.
- Local storage governance and remote GPU compute limits.

---

## 4. Troubleshooting & FAQ

| Issue / Message | Probable Cause | Recommended Resolution |
| :--- | :--- | :--- |
| `🔴 Backend Offline` | FastAPI service is not running on port 8000. | Start FastAPI using `python -m uvicorn app.main:app --port 8000`. |
| `⏳ Pending Indexing (Not Searchable)` | Document has been uploaded and chunked, but vector embeddings have not yet been synchronized. | Normal behavior. Chunks will be searchable once indexed in ChromaDB. |
| `⚡ Colab GPU Standby` | Remote Google Colab GPU server is offline or tunnel is closed. | Normal development state. Grounded evidence is retrieved; full text synthesis will resume when Colab runtime is active. |
| `HTTP 413: Payload Too Large` | Uploaded document exceeds the 10 MB limit. | Compress or split the document to stay below 10 MB. |
| `HTTP 400: Unsupported File Type` | Uploaded file is not `.pdf`, `.txt`, or `.md`. | Convert document to supported Markdown, plain text, or standard PDF format. |
