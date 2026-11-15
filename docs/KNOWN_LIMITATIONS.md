# Known System Limitations — Customer Support Intelligence Platform

**Release Version:** `v1.0.0-rc1`  
**Classification:** Controlled Pilot Ready  
**Date:** November 16, 2026  

---

## 1. Grounding & Algorithmic Limitations

### 1.1 Similarity Scores Are Not Calibrated Probabilities
- Cosine similarity scores between query embeddings and retrieved chunks indicate spatial proximity in a 384-dimensional vector space.
- **Warning:** A relevance score of `0.85` does **not** mean there is an 85% probability that the retrieved passage is factually true or answers the query. Similarity magnitude is influenced by sentence length, phrasing, and lexical density. Grounding validity must be established through the Universal Evidence Sufficiency Gate and Citation Validator.

### 1.2 Citation ID Validity Does Not Equal Semantic Entailment
- The system programmatically validates that cited chunk IDs exist, that source document metadata is intact, and that the cited snippet text appears in the knowledge base.
- While this prevents fabricated citation keys, syntactic validation alone does not guarantee semantic entailment. A human reviewer or formal entailment check is required to verify that the cited passage fully entails subtle technical conclusions.

### 1.3 Heuristic Decision Boundaries
- The Universal Evidence Sufficiency Gate employs empirical similarity floors ($s \ge 0.280$ general, $s \ge 0.350$ aspect-specific) and entity-aspect co-occurrence matching.
- **Failure Modes:** In queries featuring unusual grammatical structures, novel technical synonyms not present in the matching vocabulary, or metaphorical language, the automated gate may occasionally misclassify evidence status.

---

## 2. Dataset Boundedness & Generalization Constraints

### 2.1 Bounded by Evaluated Datasets
- The system was evaluated on canonical enterprise documentation (ApexPrint product manuals, troubleshooting guides, warranty agreements, FAQs, engineering data).
- While the architecture is domain-agnostic, performance metrics from the evaluated suites cannot be assumed to generalize identically to entirely different disciplines (e.g. legal contracts, clinical medicine, or financial tax codes) without re-benchmarking.

### 2.2 Historical Results Are Not Future Guarantees
- A 100% exact match accuracy on the 50-question blind held-out evaluation suite demonstrates that the evidence gate resolved known failure modes. It does not constitute a guarantee that the system will never make an error on novel, unconstrained inputs.

### 2.3 Human Evaluation Status
- While programmatic claim entailment audits were conducted across all 142 evaluation claims, comprehensive double-blind human subject matter expert (SME) evaluations remain in `PENDING` status pending enterprise pilot review.

---

## 3. Operational & Compute Infrastructure

### 3.1 Synthesis Execution Path Disclosures
- **Local Deterministic Synthesis:** The default verified execution path in local and offline environments assembles verified verbatim excerpts into structured Markdown sections. It does not generate conversational, generative language.
- **Remote Mistral Inference:** Generating fluent natural language requires an active, authenticated remote GPU endpoint (e.g., Google Colab with Mistral-7B-Instruct-v0.3 in 4-bit NF4 quantization). If the remote endpoint is offline, the system safely falls back to local synthesis.

### 3.2 Ingestion & Document Formatting
- Maximum file size per upload: **10 MB** (HTTP 413).
- Supported file types: `.pdf`, `.txt`, `.md`.
- Scanned PDF documents consisting solely of raster images without embedded OCR text layers will produce zero extractable text and will be rejected.
- Encrypted or password-protected PDFs are not supported.

---

## 4. Security & Deployment Safeguards

### 4.1 CORS & Authentication Prior to Public Deployment
- In development and local demonstration mode, the FastAPI backend is configured with permissive CORS (`allow_origins=["*"]`) to facilitate local React frontend development on port 5173.
- **Caution:** Prior to exposing the application to public internet traffic or enterprise intranets, CORS must be restricted to authorized origin domains, and enterprise authentication (e.g. OAuth 2.0 / SSO) must be enabled.

### 4.2 Production-Scale Reliability
- While the application passes all 233 unit and integration tests, passing unit tests alone does not establish production-scale resilience against high-concurrency traffic spikes, distributed denial-of-service attacks, or multi-tenant database partitioning.
