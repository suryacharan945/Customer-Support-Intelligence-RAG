# Stage 8 Phase 4: Rigorous Retrieval, Grounding, and Answer Quality Evaluation Report

**Evaluation Date**: 2026-11-14  
**Project**: Customer Support Intelligence / General Document Intelligence Platform  
**Active Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Git Commit Baseline**: `dcde878` (Phase 3.1)  
**Execution Environment**: Windows Local Python 3.13.9, ChromaDB persistent vector store, BM25Okapi keyword index  
**Benchmark Scope**: 50 Ground-Truth Questions across 8 Question Taxonomies and 10 Knowledge Base Documents  

---

## 1. Executive Summary

Stage 8 Phase 4 conducts an empirical, technically rigorous evaluation of the RAG and Multi-Context RAG pipelines.
Unlike previous evaluations that focused either exclusively on synthetic printer customer-support queries (Stage 7B) or on a single document (Stage 8 Phase 2.1), this benchmark exercises the complete platform across technical architecture, software engineering, research documentation, quantitative metrics, hardware troubleshooting, warranty policies, and out-of-domain edge cases.

### Key Empirical Findings:
1. **Multi-Context RAG improves top-5 retrieval recall and nDCG**:
   - **Multi-Context RAG** achieves **75.19% Recall@5**, **0.2267 Precision@5**, and **0.5980 nDCG@5**, outperforming both Dense Baseline (74.07% Recall@5, 0.5889 nDCG@5) and Unconstrained Hybrid (74.07% Recall@5, 0.5903 nDCG@5).
2. **Dense Baseline achieves slightly higher top-1 rank for direct lookups**:
   - For single-chunk factual queries, Dense Baseline achieves **0.5941 MRR** and **0.3296 Recall@1** (versus 0.5889 MRR and 0.2963 Recall@1 for Multi-Context). This confirms the classic information retrieval tradeoff: RRF fusion occasionally interleaves strong keyword matches from secondary sections into the top ranks.
3. **Zero fabricated citations**:
   - 100% of asserted citations across all 50 questions point to real, uninvented chunks delivered in retrieved context containers (**100.0% Citation Source Integrity**).
4. **Answer Fact Completeness**:
   - Supported questions achieved **85.6% key fact completeness** using the local grounded synthesis pipeline.
5. **Critical Out-of-Domain (OOD) Abstention Gap**:
   - The platform correctly abstained on completely alien queries like culinary recipes (`P4_Q46`: 100% proper abstention).
   - However, when out-of-domain questions shared lexical tokens with indexed documents (e.g. `P4_Q47` inquiring about an *HP LaserJet* paper jam), the system suffered from **false positive grounded answers (80.0% false positive rate on OOD)** due to the absence of an absolute minimum cosine similarity threshold cut-off.

---

## 2. Benchmark Dataset Architecture & Taxonomy

The Phase 4 dataset ([evaluations/stage8_phase4/dataset/benchmark_50_questions.json](file:///C:/Users/surya/Downloads/Customer%20Support%20ChatBot/evaluations/stage8_phase4/dataset/benchmark_50_questions.json)) comprises 50 annotated queries mapped to chunk-level ground truth across all 10 indexed documents (43 total chunks):

| Question Type Taxonomy | Count | ID Range | Target Capability Evaluated |
| :--- | :--- | :--- | :--- |
| **Type A: Direct Factual** | 8 | `P4_Q01` – `P4_Q08` | Direct parameter, specification, or definition retrieval |
| **Type B: Multi-Step Synthesis** | 7 | `P4_Q09` – `P4_Q15` | Multi-step procedure, pipeline dataflow, and protocol synthesis |
| **Type C: Cross-Document Multi-Context** | 7 | `P4_Q16` – `P4_Q22` | Simultaneous evidence extraction across disjoint document files |
| **Type D: Numerical & Benchmark Extraction** | 7 | `P4_Q23` – `P4_Q29` | Exact quantitative metrics, percentages, temperatures, and thresholds |
| **Type E: Comparison Questions** | 6 | `P4_Q30` – `P4_Q35` | Side-by-side technical trade-off and product feature contrast |
| **Type F: Conflicting Info & Exclusions** | 5 | `P4_Q36` – `P4_Q40` | Resolving false assumptions, policy contradictions, and warranty exclusions |
| **Type G: Ambiguous or Partial Evidence** | 5 | `P4_Q41` – `P4_Q45` | Nuanced inquiries with incomplete, missing, or qualified premises |
| **Type H: Unsupported & Out-of-Domain** | 5 | `P4_Q46` – `P4_Q50` | Alien subjects, competitor hardware, and unanswerable queries |
| **Total** | **50** | — | **45 Supported / 5 Unsupported** |

---

## 3. Retrieval Performance: Baseline vs Hybrid vs Multi-Context

Evaluated independently on all 45 supported benchmark questions with chunk-level ground truth:

| Retrieval Metric | Mode 1: Dense Baseline | Mode 2: Hybrid Fusion | Mode 3: Multi-Context RAG | Winner / Delta (MCP vs Dense) |
| :--- | :--- | :--- | :--- | :--- |
| **Recall@1** | **0.3296** | 0.3185 | 0.2963 | Dense Baseline (+0.0333) |
| **Recall@3** | 0.5593 | 0.5556 | **0.6000** | **Multi-Context RAG (+0.0407)** |
| **Recall@5** | 0.7407 | 0.7407 | **0.7519** | **Multi-Context RAG (+0.0112)** |
| **Precision@1** | **0.4444** | 0.4222 | 0.4000 | Dense Baseline (+0.0444) |
| **Precision@3** | 0.2667 | 0.2667 | **0.2889** | **Multi-Context RAG (+0.0222)** |
| **Precision@5** | 0.2178 | 0.2178 | **0.2267** | **Multi-Context RAG (+0.0089)** |
| **MRR (Mean Reciprocal Rank)**| **0.5941** | 0.5904 | 0.5889 | Dense Baseline (+0.0052) |
| **nDCG@3** | 0.5054 | 0.5044 | **0.5239** | **Multi-Context RAG (+0.0185)** |
| **nDCG@5** | 0.5889 | 0.5903 | **0.5980** | **Multi-Context RAG (+0.0091)** |
| **Evidence Coverage@5** | **86.7%** (39/45) | 84.4% (38/45) | 84.4% (38/45) | Dense Baseline (+2.3%) |
| **Retrieval Latency (Mean)** | 3,037.97 ms* | **620.40 ms** | 642.23 ms | Hybrid (Dense+BM25) |
| **Retrieval Latency (P50)** | 766.93 ms | **615.55 ms** | 619.55 ms | Hybrid (Dense+BM25) |
| **Retrieval Latency (P95)** | 15,112.56 ms* | **704.18 ms** | 816.10 ms | Hybrid (Dense+BM25) |

*\* Note on Dense Latency: The dense evaluation ran first, absorbing the PyTorch SentenceTransformer cold-start model weight loading penalty (15.1s). Subsequent warm queries ran in ~615–760 ms.*

---

## 4. End-to-End Answer Quality and Grounding

Evaluated via `app/services/rag_service.py` across all 50 queries:

| Quality Dimension | Measured Score | Evaluation Methodology & Criteria |
| :--- | :--- | :--- |
| **Answer Fact Completeness** | **85.6%** | Automated token-level coverage of ground truth expected facts across 45 supported questions |
| **Citation ID Precision** | **100.0%** | Programmatic verification that asserted citations physically exist in candidate context blocks |
| **Citation Source Integrity** | **100.0%** | Zero invented source document filenames or fabricated page references |
| **Inappropriate Abstention Rate** | **0.0%** (0 / 45) | Zero supported questions were incorrectly rejected as unanswerable |
| **Appropriate Abstention Rate** | **20.0%** (1 / 5) | 1 out of 5 out-of-domain questions was properly rejected; 4 produced false-positive answers |
| **Overall Classification Accuracy** | **92.0%** (46 / 50)| Accurate categorization into SUFFICIENT (45) vs INSUFFICIENT (1) |

---

## 5. Abstention Evaluation & Failure Case Analysis

A critical objective of Phase 4 was auditing whether the system honestly abstains when presented with out-of-domain or unanswerable queries:

| Query ID | Query Text | Expected Status | Actual Status | System Outcome | Failure Root Cause Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `P4_Q46` | *"What is the traditional recipe for Hyderabadi chicken dum biryani?"* | `INSUFFICIENT` | `INSUFFICIENT` | **PASS** (Honest Abstention) | Complete semantic divergence resulted in zero matching domain cues and low lexical overlap. System safely abstained. |
| `P4_Q47` | *"How do you clear a paper jam on a Hewlett-Packard HP LaserJet Enterprise M608?"* | `INSUFFICIENT` | `SUFFICIENT` | **FAIL** (False Positive Answer) | Keyword overlap with "paper jam" and "clear" matched ApexPrint ProX-400 Error E-101 chunk. System lacked brand entity gating. |
| `P4_Q48` | *"What is the distance between the Earth and the planet Mars at closest approach?"* | `INSUFFICIENT` | `SUFFICIENT` | **FAIL** (False Positive Answer) | Top-5 chunks from Project Dossier had low similarity (~0.22), but lack of similarity threshold cut-off caused chunks to be accepted as evidence. |
| `P4_Q49` | *"Baggage allowance policies for transatlantic flights on Delta Airlines"* | `INSUFFICIENT` | `SUFFICIENT` | **FAIL** (False Positive Answer) | Matched toner cartridge maintenance chunks due to generic language; synthesizer generated an answer from irrelevant passages. |
| `P4_Q50` | *"Does the warranty cover extraterrestrial meteor strikes or nuclear radiation?"* | `INSUFFICIENT` | `SUFFICIENT` | **FAIL** (False Positive Answer) | Matched warranty exclusion chunk ("Tampering and Disassembly") and cited general exclusions rather than stating specific clause is missing. |

### Technical Recommendation for Future Work:
Implement an **absolute cosine distance gate** (e.g. reject any retrieval result with cosine distance $> 0.55$, corresponding to similarity $< 0.45$) and an **entity mismatch filter** before passing candidate passages to the synthesizer.

---

## 6. Latency Profiling & Root-Cause Decomposition

Timing breakdown across the 50-query end-to-end evaluation:

| Latency Metric | Mean | Median (P50) | P95 | Min | Max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Retrieval Latency** | 629.70 ms | 623.60 ms | 726.98 ms | 518.20 ms | 765.40 ms |
| **Local Synthesis Latency**| 11.75 ms | 11.06 ms | 20.16 ms | 8.21 ms | 31.45 ms |
| **Total Request Latency** | 646.31 ms | 642.95 ms | 751.20 ms | 532.62 ms | 792.06 ms |

### Reconciliation of Historical Timing Discrepancies:
- **Local Synthesizer**: Measured at **11.75 ms mean** (matching the ~18 ms reported in Phase 2.1 and ~35 ms reported in Phase 3 API tests).
- **Remote GPU Inference (Mistral-7B in Stage 7B)**: Took **12,385 ms to 26,514 ms** because it executed autoregressive generation across an HTTPS tunnel.
- **Browser UI Measurement (~3,600 ms)**: Occurred in the comparison view when Baseline and Multi-Context requests executed concurrently against the single-threaded development server.

---

## 7. Artifacts Created & Reproducibility Summary

The following reproducible artifacts have been generated in `evaluations/stage8_phase4/`:
1. `dataset/benchmark_50_questions.json` (50 machine-readable ground-truth questions)
2. `dataset/benchmark_50_questions.jsonl` (JSON Lines format for automated streaming)
3. `dataset/README.md` (Dataset taxonomy and ground-truth mapping documentation)
4. `retrieval_results.json` (Full metrics across Dense, Hybrid, and MCP modes)
5. `answer_quality_results.json` (End-to-end quality and completeness results)
6. `abstention_results.json` (Confusion matrix and out-of-domain failure analysis)
7. `latency_results.json` (Detailed per-query retrieval and synthesis latency breakdown)
8. `experiment_provenance.md` (Historical experiment reconciliation and metric disambiguation)
9. `human_review_template.csv` (50-row review sheet with evaluation rubrics for human auditors)
10. `limitations.md` (Analysis of threats to validity, corpus scale, and abstention boundaries)
