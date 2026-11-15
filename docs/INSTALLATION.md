# Installation & Setup Guide — Customer Support Intelligence Platform

**Release Version:** `v1.0.0-rc1`  
**Classification:** Controlled Pilot Ready  
**Date:** November 16, 2026  

---

## 1. System Requirements & Prerequisites

### 1.1 Operating System & Hardware
- **Operating System:** Windows 10/11, macOS 12+, or Ubuntu Linux 20.04+ LTS.
- **Python:** Python 3.10, 3.11, 3.12, or 3.13.
- **Node.js:** Node.js 18.x or 20.x+ (with npm 9+).
- **RAM:** Minimum 8 GB (16 GB recommended for concurrent local embedding inference).
- **Disk Space:** Minimum 5 GB free disk space.
- **GPU:** Optional. CPU inference for `all-MiniLM-L6-v2` embeddings is fully supported.

---

## 2. Step-by-Step Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/suryacharan945/Customer-Support-Intelligence-RAG.git
cd Customer-Support-Intelligence-RAG
```

### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
venv\Scripts\Activate.ps1
# On Windows Command Prompt:
venv\Scripts\activate.bat
# On macOS / Linux:
source venv/bin/activate
```

### Step 3: Install Backend Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verify backend installation:
```bash
python -c "import fastapi, chromadb, rank_bm25, pydantic; print('Backend dependencies installed successfully.')"
```

### Step 4: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Key configuration parameters in `.env`:
```ini
ENVIRONMENT=development
APP_HOST=0.0.0.0
APP_PORT=8000
API_V1_PREFIX=/api/v1
LOCAL_EPHEMERAL_CHROMA_DIR=.chroma_live
LOCAL_MAX_STORAGE_BUDGET_MB=1024
ALLOW_MOCK_FALLBACK=false
LLM_PROVIDER=local
ALLOW_LOCAL_FALLBACK=true
```

### Step 5: Initialize Knowledge Base & Vector Store
The knowledge base automatically seeds on first application startup from `data/knowledge_base/`. To manually verify or re-seed the vector store and BM25 index:
```bash
python scripts/seed_canonical_knowledge_base.py
```

### Step 6: Set Up Frontend (React + Vite)
```bash
cd web
npm install
```

Verify frontend build:
```bash
npm run build
```

---

## 3. Starting the Application

### 3.1 Starting the Backend Gateway
From the repository root (with virtual environment active):
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Base URL: `http://127.0.0.1:8000/api/v1`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/api/v1/health`

### 3.2 Starting the React Frontend
In a second terminal:
```bash
cd web
npm run dev
```
Open your browser to: **`http://localhost:5173/`**

---

## 4. Running the Test Suites

### 4.1 Backend Test Suite (Pytest)
```bash
python -m pytest tests/
```
Expected output: **233 passed** (approx. 90–100 seconds).

### 4.2 Frontend Test Suite (Vitest)
```bash
npm --prefix web test -- --run
```
Expected output: **12 passed** across 3 test files.

---

## 5. Troubleshooting Common Issues

| Issue | Root Cause | Solution |
|---|---|---|
| `Port 8000 already in use` | Another uvicorn or web service is running on port 8000. | Check running tasks with `Get-NetTCPConnection -LocalPort 8000` and stop the conflicting process, or specify `--port 8005`. |
| `Port 5173 already in use` | Vite dev server already running. | Vite automatically prompts to use port 5174, or specify `npm run dev -- --port 5174`. |
| `sqlite3.OperationalError: database is locked` | ChromaDB SQLite file accessed concurrently across multiple processes. | Ensure only one backend ASGI worker is writing to `.chroma_live`. |
| `ModuleNotFoundError: No module named 'app'` | Python path does not include the project root. | Run python commands from the repository root directory, or set `PYTHONPATH=.`. |
| `PowerShell script execution disabled` | PowerShell execution policy prevents script activation. | Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`. |
| `Vite build out of memory` | Node.js default heap space exceeded during bundling. | Run `NODE_OPTIONS="--max-old-space-size=4096" npm run build`. |
