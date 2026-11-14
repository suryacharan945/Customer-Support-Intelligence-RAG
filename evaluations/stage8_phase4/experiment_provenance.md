# Historical Experiment Provenance & Metric Reconciliation

**Date**: 2026-11-14  
**Project**: Customer Support Intelligence / General Document Intelligence Platform  
**Active Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Git Baseline**: Commit `dcde878` (Phase 3.1)

---

## 1. Experiment Registry & Provenance Matrix

| Experiment ID | Date | Execution Environment | Git Commit | Retrieval Configuration | Generation Provider | Dataset & Size | Measurement Methodology | Signal Type |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stage 4** | 2026-10-25 | Windows local pytest | `8f21a4e` | Vector (Dense only) vs Hybrid (Dense + BM25) vs MCP Partitioned | Synthetic test fixtures / mocks | 16 synthetic queries | Automated pytest assertions against synthetic ground truth | Automated / Simulated |
| **Stage 7B** | 2026-10-28 | Google Colab GPU (NVIDIA Tesla T4, 15GB VRAM) via Cloudflare Tunnel | `7b32c10` | Baseline (Dense $k=3$) vs MCP (Hybrid Dense + BM25 $k=5$) | Remote Mistral-7B-Instruct-v0.3 (4-bit NF4 quantized, ~5.2 GB VRAM) | 16 printer customer support queries | Live HTTP streaming from local client to remote Colab tunnel | Live Remote GPU Telemetry |
| **Stage 8 Phase 2.1** | 2026-11-14 | Windows local Python 3.13 | `9283e73` | Soft-category generalized hybrid retrieval (Dense + BM25Okapi + RRF $k=5$) | Local Grounded Synthesizer (`local_synthesizer.py`) | 15 queries (14 Project Dossier + 1 OOD) | Automated script (`scripts/eval_phase2_dossier.py`) evaluating grounded extraction | Automated Local Evaluation |
| **Stage 8 Phase 3** | 2026-11-14 | Windows local FastAPI (uvicorn) | `cfd5975` | Generalized MCP hybrid retrieval | Local Grounded Synthesizer | 5 multi-domain queries (Architecture, Benchmarks, Printer, Comparison, OOD) | Live FastAPI `TestClient` API requests (`scripts/verify_phase3_api_live.py`) | Live API Telemetry |
| **Stage 8 Phase 3.1** | 2026-11-14 | Windows local Chrome/Webview browser (`localhost:5173`) | `dcde878` | Generalized MCP hybrid retrieval | Local Grounded Synthesizer | 6 user journeys (Tests A through F) | End-to-end browser subagent automation with full DOM inspection and PNG screenshots | Live Browser E2E |
| **Stage 8 Phase 4** *(Current)* | 2026-11-14 | Windows local Python 3.13 & FastAPI | `dcde878` | 1. Dense Baseline ($k=5$)<br>2. Hybrid Dense+BM25<br>3. MCP Hybrid + Dynamic Routing | Baseline vs Local Grounded Synthesizer | 50 multi-domain questions (8 categories) | Chunk-level Recall@K, Precision@K, MRR, nDCG@K, citation claim entailment, latency decomposition | Automated Benchmark + Human Review Rubric |

---

## 2. Reconciliation of Historical Metric Discrepancies

### A. The 41.25% vs 100% Citation Precision Discrepancy in Stage 7B
In historical project reports, two seemingly contradictory figures were presented for Stage 7B:
- **Figure 1**: Multi-Context RAG citation precision was reported as **41.25%** (compared to 100% for Baseline).
- **Figure 2**: The citation validation engine reported **100% citation validity** with 0 hallucinated citations.

#### Root Cause Analysis:
An audit of `evaluation/stage7b_live_results.json` and `scripts/recompute_citation_metrics.py` reveals the mathematical cause:
1. In Stage 7B's initial evaluator (`evaluation/stage7_evaluator.py`), the variable named `citation_precision` was computed as:
   $$\text{"citation\_precision"} = \frac{|\text{model asserted citations}|}{|\text{candidate passages delivered in prompt}|}$$
2. For Baseline RAG, only 1 candidate passage was supplied ($k=1$), and the model cited that 1 passage: $\frac{1}{1} = 1.0$ (100%).
3. For Multi-Context RAG, 5 candidate passages were supplied ($k=5$), and the model cited on average 2.06 passages: $\frac{2.06}{4.88} = 41.25\%$.
4. **Conclusion**: The 41.25% metric was strictly **Candidate Context Utilization Rate**, NOT citation precision. Every single citation that Mistral-7B generated physically corresponded to a genuine chunk in the candidate container (**100% Citation Source Validity**).
5. In Phase 4, we strictly separate **Citation Precision** ($\frac{|\text{valid citations}|}{|\text{asserted citations}|}$) from **Context Utilization** ($\frac{|\text{cited chunks}|}{|\text{retrieved candidate chunks}|}$).

---

### B. Latency Timing Inconsistencies Across Reports
Historical documents report wildly disparate latency values:
- **Stage 7B Live Colab**: Baseline generation: `12,385.87 ms` (~12.4s); Multi-Context generation: `26,514.24 ms` (~26.5s).
- **Stage 8 Phase 2.1 Local Synthesizer**: Local synthesis: `18.2 ms`; Retrieval: `580.4 ms`.
- **Stage 8 Phase 3 Live API**: Total HTTP: `1,243.5 ms` (Retrieval: `1,161.5 ms`, Synthesis: `39.1 ms`).
- **Stage 8 Phase 3.1 Browser UI**: Single query: `166.15 ms` / `301.99 ms`; Comparison view: `6,513.4 ms` / `3,676.5 ms`.

#### Root Cause Analysis:
These figures measured completely different execution paths and execution environments:
1. **Remote GPU Inference (Stage 7B)**: Ran Mistral-7B-Instruct-v0.3 across a Cloudflare tunnel to a remote Google Colab Tesla T4 GPU. Network latency, tokenizer latency, and auto-regressive token generation for ~350 tokens at 15–25 tokens/second naturally took **12 to 26 seconds**.
2. **Local Python Synthesizer (Stage 8 Phase 2.1 & 3 API)**: Operates 100% offline in Python memory using regex and sentence scoring. Execution time is **15 to 40 milliseconds**.
3. **ChromaDB / BM25 Cold Start vs Warm Cache**:
   - First query on cold collection initializes the SentenceTransformer model and BM25 index: **1,000–3,000 ms**.
   - Subsequent warm queries: **150–500 ms**.
4. **Browser UI Comparison Latency**: In the React frontend comparison page, Baseline and Multi-Context queries were fired concurrently to the backend server. The concurrent retrieval and synthesis resulted in queued execution and thread contention, measuring **3.6s to 6.5s** total round-trip time.

In Phase 4, every latency measurement explicitly specifies the hardware, provider, cold/warm state, retrieval component, and synthesis component.
