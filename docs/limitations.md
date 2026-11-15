# System Boundaries & Limitations — Customer Support Intelligence Platform

**Release Version:** `v1.0.0-rc1`  
**Classification:** Release Candidate / Controlled Pilot Ready  
**Date:** 2026-11-16  

---

## 1. Knowledge Boundedness & Domain Scope

The Customer Support Intelligence Platform is an **evidence-grounded system**. It is strictly bounded by the documents indexed in the local knowledge base or uploaded by authorized users.

### 1.1 Out-of-Scope Domains
1. **Live Internet & Real-Time Data:** The platform does not crawl live websites, real-time web news, or current stock indices.
2. **Third-Party Commercial Pricing:** The knowledge base does not track retail marketplace pricing, eBay bids, Amazon coupons, or distributor wholesale discounts unless explicitly uploaded as internal pricing sheets.
3. **Internal Cryptographic Credentials:** The system strictly rejects requests for administrative credentials, private cryptographic keys, or security tokens.
4. **Unindexed Geographical Facilities:** Regional service depots or international addresses outside indexed warranty documentation will correctly trigger calibrated abstention (`INSUFFICIENT`).

---

## 2. Technical & Performance Limitations

### 2.1 Cold-Start Retrieval Latency
- The initial query execution after system boot requires **~1,600 ms** due to embedding model weight loading and ChromaDB index warm-up.
- Subsequent warm queries execute in **~850 ms – 1,100 ms**.
- Multi-part and comparative queries requiring multi-stage sub-retrieval average **~2,450 ms**.

### 2.2 Uncalibrated Similarity Scores
- The `relevance_score` returned by the retrieval engine represents raw vector cosine similarity ($\in [0.0, 1.0]$) or hybrid fusion rank.
- **Warning:** Raw similarity scores must **not** be interpreted as mathematical probabilities of factual correctness. Grounding validity is established by the Universal Evidence Sufficiency gate and Citation Validator, not similarity magnitude alone.

### 2.3 Synthesis Modality (Offline vs Remote LLM)
- **Local Grounded Synthesis Mode:** In the absence of an active remote GPU LLM endpoint (e.g. Google Colab or Ollama), the system relies on native deterministic synthesis. This mode produces rigorous, verbatim-grounded technical answers but does not engage in colloquial banter or stylistic rewriting.
- **Remote LLM Mode:** When connected to an instruction-tuned LLM (e.g. Mistral-7B-Instruct-v0.3), fluent natural language generation is achieved while retaining strict citation boundaries.

### 2.4 Document Ingestion Constraints
- Maximum file size per upload: **10 MB** (enforced by HTTP 413).
- Supported file types: `.pdf`, `.txt`, `.md`.
- Legacy binary formats (`.doc`, `.xls`, `.zip`, `.exe`) are rejected with HTTP 400.
- Scanned PDF images without an embedded OCR text layer will produce zero extractable text and trigger an empty document error.

---

## 3. Recommended Operational Safeguards

1. **Human-in-the-Loop for Safety-Critical Tasks:** While the system achieves a 0.0% false acceptance rate on the benchmark suite, physical printer disassembly instructions should always be cross-referenced with authorized field technician guides.
2. **Periodic Snapshot Backups:** Always run `python scripts/backup_to_drive.py` prior to large-scale document re-indexing.
3. **Storage Quota Monitoring:** Maintain local disk usage below the 1,024 MB threshold to prevent automatic ephemeral cache purging.
