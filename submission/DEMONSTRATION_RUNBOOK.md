# Reproducible Demonstration Runbook

**Project**: Customer Support Intelligence Assistant (RAG + Multi-Contextual Prompting)  
**Target Environment**: Windows 11 / PowerShell 5.1+ / Python 3.10–3.13  
**Repository**: `C:\Users\surya\Internship_RAG_MCP_Capstone`  
**Primary Backup & Storage**: `G:\My Drive\Internship_RAG_MCP_Capstone`  
**Document Revision**: 2.0 (Post-Stage 8B Freeze)  

---

## 1. System Requirements & Prerequisites

### 1.1 Host Environment
- **Operating System**: Microsoft Windows 10/11 64-bit
- **Shell**: Windows PowerShell or PowerShell 7
- **Python Version**: Python 3.10 to 3.13 (64-bit)
- **Local Storage**: ~500 MB for repository and dependencies (0 GB local model storage required)
- **Primary Cloud Storage**: Google Drive mounted as `G:\` (Drive for desktop)

### 1.2 Remote Compute (Google Colab)
- Google account with access to Google Colab (Free tier with standard T4 GPU is sufficient)
- Colab notebook: `notebooks/02_colab_mistral_rag_inference.ipynb`

---

## 2. Environment Setup & Dependency Installation

Open Windows PowerShell and navigate to the project directory:

```powershell
# 1. Navigate to project repository
cd C:\Users\surya\Internship_RAG_MCP_Capstone

# 2. Verify Python version (must be >= 3.10)
python --version

# 3. Create and activate a clean virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 4. Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Verify automated regression suite (all 148 tests must pass)
python -m pytest tests/
```

---

## 3. Remote GPU Inference Setup (Google Colab)

To enable live Mistral-7B inference without downloading 15 GB of model weights locally:

1. Open a web browser and navigate to [Google Colab](https://colab.research.google.com).
2. Upload the notebook: `notebooks/02_colab_mistral_rag_inference.ipynb`.
3. In Colab, navigate to **Runtime > Change runtime type** and select **T4 GPU** (Hardware accelerator).
4. Run Cells 1 through 7 sequentially:
   - Cell 1: Verify NVIDIA T4 GPU allocation (`nvidia-smi`).
   - Cell 2: Install dependencies (`transformers`, `bitsandbytes`, `accelerate`, `fastapi`, `uvicorn`, `pyngrok`).
   - Cell 3: Load `mistralai/Mistral-7B-Instruct-v0.3` in 4-bit NF4 quantization (~5.2 GB VRAM).
   - Cell 4: Initialize lightweight FastAPI inference service on port 8000.
   - Cell 5: Generate a cryptographically secure ephemeral API token:
     ```python
     import secrets
     COLAB_API_KEY = secrets.token_urlsafe(32)
     print(f"COLAB_API_KEY = {COLAB_API_KEY}")
     ```
   - Cell 6: Launch Cloudflare Tunnel (`cloudflared tunnel --url http://127.0.0.1:8000`).
   - Cell 7: Note the public HTTPS tunnel endpoint printed in cell output:
     `https://<ephemeral-subdomain>.trycloudflare.com/v1`

---

## 4. Local Configuration & Credential Setup

Create or update your local `.env` file in the root of `C:\Users\surya\Internship_RAG_MCP_Capstone`. **Never commit this file to Git**:

```ini
# Core Configuration
ENVIRONMENT=development
ALLOW_MOCK_FALLBACK=true

# Remote GPU Inference Provider
LLM_PROVIDER=colab_remote
COLAB_API_ENDPOINT=https://<your-colab-subdomain>.trycloudflare.com/v1
COLAB_API_KEY=<your-colab-api-key>

# Service Ports
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
FASTAPI_BASE_URL=http://127.0.0.1:8000
```

Verify connectivity to the Colab endpoint before launching the local application:

```powershell
# Probe remote endpoint health
python -c "
import os, httpx
from dotenv import load_dotenv
load_dotenv()
endpoint = os.getenv('COLAB_API_ENDPOINT')
key = os.getenv('COLAB_API_KEY')
headers = {'Authorization': f'Bearer {key}'}
r = httpx.post(f'{endpoint}/chat/completions', json={'messages': [{'role': 'user', 'content': 'Ping'}], 'max_tokens': 5}, headers=headers, timeout=15)
print('Remote GPU Status:', r.status_code, r.json().get('choices', [{}])[0].get('message', {}).get('content', ''))
"
```

---

## 5. Local Application Startup

Open two separate PowerShell terminal windows:

### Terminal 1: Launch FastAPI Backend
```powershell
cd C:\Users\surya\Internship_RAG_MCP_Capstone
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Expected Output*:
`INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`  
Interactive Swagger documentation is accessible at `http://127.0.0.1:8000/docs`.

### Terminal 2: Launch Streamlit Frontend
```powershell
cd C:\Users\surya\Internship_RAG_MCP_Capstone
streamlit run frontend/app.py --server.port 8501
```
*Expected Output*:
`Local URL: http://localhost:8501`  
The web browser will automatically open to the Customer Support Assistant interface.

---

## 6. Demonstration Workflows

### 6.1 Demonstration 1: Baseline Single-Channel RAG
1. In the Streamlit UI sidebar, ensure the backend status badge indicates **🟢 Backend Online**.
2. Navigate to **💬 Chat Assistant**.
3. In the **⚙️ Retrieval Configuration** expander, set:
   - **RAG Retrieval Strategy**: `Baseline (Dense Only)`
   - **Top-K Chunks**: `5`
4. Enter the inquiry:
   ```text
   What is the maximum print speed of the ApexPrint ProX-400?
   ```
5. Click **Submit Inquiry** (or press Enter).
6. **Observed Behavior**:
   - The response generates in ~10 seconds.
   - The UI displays the provider badge (`TEST_MOCK_MODE` / `colab_remote`).
   - Notice that Baseline unconstrained retrieval may return an abstention or generic troubleshooting excerpt due to lack of category filtering.

---

### 6.2 Demonstration 2: Multi-Context MCP Hybrid RAG
1. Switch the radio toggle to:
   - **RAG Retrieval Strategy**: `Multi-Context (MCP Hybrid)`
2. Enter the complex cross-category inquiry:
   ```text
   My printer jammed with error E-101 and I used non-OEM toner. Is the repair covered under warranty?
   ```
3. Click **Submit Inquiry**.
4. **Observed Behavior**:
   - Total generation time is ~20–25 seconds.
   - Category badge indicates dual routing: `['warranty', 'troubleshooting']`.
   - The response is cleanly formatted into structured markdown sections:
     1. *Executive Summary / Direct Answer*
     2. *Step-by-Step Resolution*
     3. *Warranty & Policy Cross-Reference*
     4. *Verified Source Citations*
   - Citations expand to show genuine chunk IDs (`doc_trou_...` and `doc_warr_...`).

---

### 6.3 Demonstration 3: Side-by-Side Comparison View
1. In the sidebar radio menu, select **⚖️ Mode Comparison**.
2. Select Quick Inquiry Option 1 or input:
   ```text
   Can I return an opened printer if the printhead is defective, and what is the return window?
   ```
3. Click **🚀 Run Comparative Analysis**.
4. **Observed Behavior**:
   - Both Mode A (Baseline) and Mode B (MCP) execute concurrently.
   - Mode A displays a short single-category answer (~10s).
   - Mode B synthesizes across warranty policy and troubleshooting steps with 100% genuine citation verification (~25s).

---

### 6.4 Demonstration 4: Document Lifecycle & Searchability Invariant
1. Navigate to **📄 Document Management**.
2. Upload a test Markdown file (`demo_test.md`).
3. Observe the newly created table row:
   - Status badge shows: **`PENDING_EMBEDDING`** (Amber).
   - Searchable column shows: **`False`** (Red cross).
4. Perform a search query in Chat Assistant; demonstrate that the uploaded document cannot be retrieved until batch vector indexing has been completed.
5. In Document Management, click **🗑️ Delete**; confirm the file is purged atomically.

---

### 6.5 Demonstration 5: Active Learning Feedback Loop
1. Under any generated response in **💬 Chat Assistant**, locate the feedback widget.
2. Select **5 Stars**.
3. Enter comment: *"Accurate cross-category policy synthesis."*
4. Click **Submit Feedback**.
5. Observe green confirmation message: `"Feedback recorded"`.
6. Inspect `app/data/feedback_logs.jsonl` to verify the turn, query ID, rating, and comment were appended.

---

### 6.6 Demonstration 6: Failure Handling & Provider Resilience
1. In the Streamlit sidebar, open **⚙️ Connection Settings**.
2. Change the FastAPI Base URL to an invalid port: `http://127.0.0.1:9999`.
3. Observe that the sidebar immediately displays:
   ```
   🔴 Backend Offline
   Target: http://127.0.0.1:9999
   Start FastAPI to enable live querying.
   ```
4. Demonstrate that the interface remains interactive and does not crash with an unhandled exception.
5. Restore the URL to `http://127.0.0.1:8000`.

---

## 7. Shutdown & Cleanup

When the demonstration is complete:

1. In Terminal 2 (Streamlit): Press `Ctrl + C` to stop the frontend server.
2. In Terminal 1 (FastAPI): Press `Ctrl + C` to stop the backend server.
3. In Google Colab: Click **Runtime > Disconnect and delete runtime** to terminate the GPU instance and release cloud resources.
4. Verify port release in PowerShell:
   ```powershell
   Get-Process -Name "python", "uvicorn", "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
