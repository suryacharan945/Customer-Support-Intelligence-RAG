# Stage 10 — Application User Guide & Demonstration Manual
**Project**: Multi-Context Intelligent RAG System — Customer Support Intelligence Platform  
**Document**: STAGE_10_USER_GUIDE.md  
**Version**: 1.0.0  
**Date**: October 2026  
**Status**: APPROVED & PUBLISHED  

---

## 1. Introduction

Welcome to the **ApexPrint Customer Support Intelligence Platform**. This manual guides users, evaluators, and internship advisors through operating both the primary **React Web Application** and the legacy **Streamlit Fallback Interface**.

---

## 2. Launching the Platform

### 2.1 Quick Start (Simultaneous Multi-Service Launch)

To start the complete platform on Windows, open a PowerShell terminal in the repository root (`C:\Users\surya\Internship_RAG_MCP_Capstone`):

```powershell
# 1. Start the FastAPI Backend Server (Port 8000)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. In a second terminal, start the React Web Application (Port 5173)
cd web
npm run dev

# 3. Optional: In a third terminal, start the Streamlit Fallback (Port 8501)
python -m streamlit run frontend/app.py --server.port 8501
```

Once launched:
- **Primary React Web Application**: Navigate to `http://localhost:5173/`
- **FastAPI Interactive Swagger Docs**: Navigate to `http://127.0.0.1:8000/docs`
- **Streamlit Fallback Interface**: Navigate to `http://localhost:8501/`

---

## 3. Navigating the React Web Application

```
+---------------------------------------------------------------------------------------+
|  [Logo] ApexPrint AI     [Status: Ready (5/5)]  [Theme: Dark/Light]  [Drive: Synced]  |
|---------------------------------------------------------------------------------------|
|  [Dashboard]      Overview KPI cards, vector store status, and quick-start actions   |
|  [Support Chat]   Multi-turn conversational assistant with citation verification     |
|  [Knowledge Base] Document upload dropzone, filterable table, chunk inspector         |
|  [Dual Compare]   Side-by-side Baseline vs Multi-Context prompt execution             |
|  [Analytics]      Interactive Recharts graphs of live benchmark evaluations           |
|  [How It Works]   Visual educational guide on RAG & Multi-Context Prompting           |
|  [System Status]  5-subsystem live probe, diagnostic telemetry, and raw JSON export   |
+---------------------------------------------------------------------------------------+
```

### 3.1 Overview Dashboard (`/`)
- **Key Performance Indicators**: Shows real-time count of active documents, searchable chunks, vector store health, and free disk space.
- **Hero Section**: 3D interactive knowledge particle network illustrating document clustering.
- **Quick Action Links**: Direct buttons to launch a chat session, upload manuals, or inspect benchmark metrics.

### 3.2 AI Support Chat (`/chat`)
- **RAG Mode Switcher**: Easily switch between **Baseline RAG** (single-channel dense vector retrieval) and **Multi-Context MCP** (multi-category query decomposition and multi-channel hybrid retrieval).
- **Submitting Questions**: Type your inquiry in the message input and press `Enter` or click the Send button.
- **Inspect Citations**: Click on any citation card to view the exact snippet, source document filename, relevance score, and verification status.
- **Submit Feedback**: Click the thumbs-up or thumbs-down icon on any assistant response to submit ratings, corrections, or hallucination reports directly into the feedback log.

### 3.3 Knowledge Base Studio (`/documents`)
- **Document Registry**: Search and filter uploaded support documents by filename or category (`product_manual`, `troubleshooting`, `warranty`, `faq`).
- **Drag-and-Drop Upload**: Drop text or markdown files into the upload zone, select a category, and trigger automatic chunking and Chroma vector indexing.
- **Inspect Chunks**: Click "Inspect Chunks" on any document row to view chunk count, file size, content hash, and lifecycle state.
- **Delete Document**: Safely delete documents with confirmation dialogs that report affected chunks.

### 3.4 Dual-Channel RAG Comparison (`/compare`)
- **Side-by-Side Analysis**: Enter a support question to execute both Baseline and Multi-Context pipelines simultaneously.
- **Comparative Metrics**: Compare retrieval latency, number of citations retrieved, and citation precision directly in a split-screen view.

### 3.5 Benchmark Analytics (`/analytics`)
- **Frozen Benchmark Graphs**: Explore real experimental data comparing Baseline and Multi-Context modes across 32 live evaluations and 10 held-out test queries.
- **Interactive Tooltips**: Hover over Recharts bars to view exact millisecond timings, chunk counts, and true citation precision metrics.

### 3.6 How It Works Guide (`/how-it-works`)
- **Educational Walkthrough**: Understand the technical differences between dense single-channel retrieval and Multi-Context Prompting through diagrams and comparative tables.

### 3.7 System Status Probe (`/status`)
- **5-Subsystem Checklist**: Real-time diagnostic verification of Storage, Ingestion Manifest, Vector Store (ChromaDB), Embedding Provider, and LLM Inference Gateway.
- **Raw Telemetry**: View and copy full JSON payload for reporting and audit logging.

---

## 4. Troubleshooting & FAQ

- **Q: Why is port 3000 not used?**  
  *A*: On Windows developer machines running Docker, port 3000 is often reserved by Docker Desktop backend services. The React Vite server is configured to use port `5173`, with an internal proxy that forwards `/api` requests directly to FastAPI on port `8000`.
- **Q: How do I switch between dark and light themes?**  
  *A*: Click the Sun/Moon toggle icon in the top-right header. Your theme preference is automatically remembered across browser sessions via `localStorage`.
- **Q: What happens if the remote Colab GPU is offline?**  
  *A*: The platform operates in hybrid fallback mode. Retrieval and citation verification continue to run with 100% accuracy, while answers are generated via the local fallback provider or marked with appropriate evidence status indicators.
