# Evaluator Demonstration Script — 5-to-7 Minute Walkthrough

**Platform:** Customer Support Intelligence & Document Intelligence Platform  
**Release Version:** `v1.0.0-rc1`  
**Classification:** Controlled Pilot Ready  
**Target Audience:** Technical Reviewers, Evaluators, Engineering Leadership  
**Demonstration Time:** 5–7 Minutes  

---

## 1. Preparation & Service Startup (1 Minute)

Open two terminal windows:

### Terminal 1: Backend Gateway
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
*Expected console confirmation:* `Uvicorn running on http://127.0.0.1:8000`

### Terminal 2: React Frontend
```bash
cd web
npm run dev
```
*Expected console confirmation:* `Local: http://localhost:5173/`

Open your web browser to: **`http://localhost:5173/`**

---

## 2. Step-by-Step Demonstration Sequence

### Step 1: System Introduction & Status (0:00 – 0:40)
- **On Screen:** Point out the dark-mode dashboard titled *"ApexPrint AI Intelligence — Multi-Context Support Platform"*.
- **Show Telemetry:** Highlight the top status pills showing `🟢 Backend Online`, `44 Indexed Chunks`, and active mode indicator.
- **Explain Verbally:** *"This is an evidence-grounded document intelligence assistant. Unlike standard RAG systems that hallucinate when information is missing, this architecture enforces strict evidence sufficiency, query decomposition, and claim-level citation validation."*

### Step 2: Document Ingestion & Searchability Gating (0:40 – 1:50)
- **Action:** Click the **Knowledge Base** tab in the sidebar navigation.
- **Upload:** In the Upload zone, select category `Engineering` and upload a test document (e.g. `tests/sample_doc.md` or a local technical text file).
- **Show on Screen:** The document is registered with `lifecycle_status: pending_index` and `is_searchable: false`.
- **Explain Verbally:** *"Notice the 6-state document lifecycle. The document is uploaded and chunked, but it is deliberately locked from search to prevent unindexed or corrupt data from polluting queries."*
- **Action:** Click **Index Document**. Status transitions to `indexed` and `is_searchable: true`.

### Step 3: Direct Factual Query & Multi-Context Retrieval (1:50 – 2:30)
- **Action:** Return to **Chat** and enter:
  ```text
  What is the standard print resolution of the ApexPrint ProX-400?
  ```
- **Show on Screen:**
  - `🟢 Sufficient Grounding` badge appears.
  - Executive summary answers: `Up to 1200 x 1200 dpi`.
  - Citations cite `apexprint_prox400_user_manual.md` with chunk ID `doc_prod_de7386b29af7_c0001`.
- **Explain Verbally:** *"The system routes the query to the product manual domain, fuses dense vector search with BM25 keyword matching, and confirms evidence sufficiency before answering."*

### Step 4: Multi-Part Query Decomposition (2:30 – 3:10)
- **Action:** In the query box, enter:
  ```text
  What is the standard print resolution of the ApexPrint ProX-400 and what is its maximum monthly duty cycle?
  ```
- **Show on Screen:**
  - System decomposes the conjunction clause into two sub-questions.
  - Answers both specifications: 1200 x 1200 DPI resolution and 80,000 page monthly duty cycle.
- **Explain Verbally:** *"The query decomposer resolves the pronoun 'its' to the ProX-400, retrieves evidence for both aspects, and synthesizes a dual-grounded answer."*

### Step 5: Partial Support & Hallucination Prevention (3:10 – 4:00)
- **Action:** Enter a partially supported query:
  ```text
  What is the monthly duty cycle of the ProX-400 and what is its retail price on Amazon?
  ```
- **Show on Screen:**
  - **`🟡 Partial Evidence`** badge renders.
  - Section 1 answers the documented duty cycle (80,000 pages).
  - Section 2 under **Missing Information & Limitations** states: *Commercial retail pricing on Amazon is undocumented in the knowledge base.*
- **Explain Verbally:** *"A standard RAG system would guess an Amazon price based on lexical proximity. Here, the evidence gate identifies that the retail price aspect is ungrounded, explicitly disclosing the limitation while answering the supported clause."*

### Step 6: Unsupported Query & Calibrated Abstention (4:00 – 4:40)
- **Action:** Enter an unsupported out-of-domain query:
  ```text
  What is the return warehouse shipping street address in Tokyo Japan for RMA claims?
  ```
- **Show on Screen:**
  - **`🔴 Insufficient Evidence`** badge renders.
  - Calibrated abstention response: *"Based on the available documentation, insufficient evidence was found in the knowledge base to answer this inquiry. Regional depot for 'Tokyo' is not documented."*
- **Explain Verbally:** *"Instead of fabricating a plausible street address, the system formally abstains."*

### Step 7: Inspecting Evidence & Citation Verification (4:40 – 5:20)
- **Action:** On any answered query, click **"Inspect Evidence"** on a citation pill.
- **Show on Screen:** The sliding **Evidence Drawer** opens from the right.
- **Point out:**
  - Document Source: `apexprint_prox400_user_manual.md`
  - Chunk ID: `doc_prod_de7386b29af7_c0001`
  - Relevance Score: 78% (with clear disclosure that this is a vector similarity signal, not a probability)
  - Verbatim excerpt text directly highlighted.

### Step 8: Active Learning Feedback (5:20 – 5:50)
- **Action:** Click **"Rate & Review"** on the answer card.
- **Action:** Select 5 stars, add a note (*"Verified technical specifications"*), and click **Submit Feedback**.
- **Show on Screen:** Success toast notification; feedback is stored in the persistent active learning queue.

### Step 9: Summary & Limitations Disclosure (5:50 – 6:30)
- **Summary:** Conclude with the benchmark metrics: 100% blind test accuracy, 0.0% false acceptance rate, and 233 passing backend tests.
- **Limitations:** Remind reviewers that similarity scores are relevance signals, not probabilities, and that production internet deployment requires enterprise authentication.

---

## 3. Demo Failure Recovery Runbook

| Failure Symptom | Immediate Recovery Action |
|---|---|
| Frontend displays *Backend Disconnected* | Check Terminal 1 to ensure uvicorn is running. If terminated, restart with `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. |
| Query returns 500 Internal Error | Verify `.chroma_live` exists. If corrupted, re-seed in 5 seconds via `python scripts/seed_canonical_knowledge_base.py`. |
| Browser shows blank page | Refresh with `Ctrl+Shift+R` to clear cached frontend bundles. |
