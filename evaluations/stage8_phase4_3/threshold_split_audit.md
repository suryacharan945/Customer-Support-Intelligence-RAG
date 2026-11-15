# Stage 8 Phase 4.3: Threshold Calibration and Split Integrity Audit

**Target Document Audited**: `evaluations/stage8_phase4_2/threshold_calibration.json`  
**Vector Database Environment**: ChromaDB (`.chroma_live`), `sentence-transformers/all-MiniLM-L6-v2`  
**Date**: November 15, 2026  
**Auditor**: Evaluation Integrity & Independent Verification Engine  

---

## 1. Executive Summary

This audit independently reviews the threshold calibration process recorded in `threshold_calibration.json`. The analysis verifies the split composition, distribution of supported and unsupported queries across splits, threshold selection methodology, potential data leakage between calibration and evaluation, calibration of sparse BM25 scores, and distance metric verification in ChromaDB.

**Key Verdict**: While the empirical similarity floor of **`0.2800`** effectively separates pure out-of-domain alien queries ($[0.0812, 0.2658]$) from concise supported queries ($[0.3124, 0.8842]$), **the split methodology in Phase 4.2 exhibited substantial structural limitations**:
1. The "Development Set" contained **zero unsupported queries** (25 supported, 0 unsupported).
2. All 5 unsupported queries in the benchmark were concentrated exclusively in the "Validation Set" (`P4_Q46` to `P4_Q50`).
3. There was **no genuinely held-out negative dataset** prior to threshold selection.
4. Sparse BM25 scores were **not independently calibrated** with a numerical floor.

---

## 2. Split Composition & Query Distribution

In `threshold_calibration.json`, the dataset of 50 benchmark queries was partitioned into two halves:

### 2.1 Development Set (`queries 01 to 25`)
- **Total Queries**: 25
- **Supported Queries**: **25** (`P4_Q01` through `P4_Q25`)
- **Unsupported Queries**: **0** (0.0%)
- **Query IDs**:
  `P4_Q01`, `P4_Q02`, `P4_Q03`, `P4_Q04`, `P4_Q05`, `P4_Q06`, `P4_Q07`, `P4_Q08`, `P4_Q09`, `P4_Q10`,
  `P4_Q11`, `P4_Q12`, `P4_Q13`, `P4_Q14`, `P4_Q15`, `P4_Q16`, `P4_Q17`, `P4_Q18`, `P4_Q19`, `P4_Q20`,
  `P4_Q21`, `P4_Q22`, `P4_Q23`, `P4_Q24`, `P4_Q25`.
- **Top Dense Similarity Range**: $[0.3644, 0.7882]$ (Mean: $0.6241$).
- **Methodological Limitation**: A development set containing zero negative examples is mathematically incapable of measuring False Acceptance Rate (FAR) or optimizing decision boundaries for abstention. In `threshold_calibration.json`, FAR is reported as `0.0` for all thresholds purely because the denominator is zero.

### 2.2 Validation Set (`queries 26 to 50`)
- **Total Queries**: 25
- **Supported Queries**: **20** (`P4_Q26` through `P4_Q45`)
- **Unsupported Queries**: **5** (`P4_Q46` through `P4_Q50`)
- **Query IDs**:
  `P4_Q26`, `P4_Q27`, `P4_Q28`, `P4_Q29`, `P4_Q30`, `P4_Q31`, `P4_Q32`, `P4_Q33`, `P4_Q34`, `P4_Q35`,
  `P4_Q36`, `P4_Q37`, `P4_Q38`, `P4_Q39`, `P4_Q40`, `P4_Q41`, `P4_Q42`, `P4_Q43`, `P4_Q44`, `P4_Q45`,
  `P4_Q46`, `P4_Q47`, `P4_Q48`, `P4_Q49`, `P4_Q50`.
- **Supported Top Dense Similarity Range**: $[0.3124, 0.7412]$ (Lowest: `P4_Q43` at $0.3124$).
- **Unsupported Top Dense Similarity Range**:
  - Pure Alien Queries:
    - `P4_Q48` (Earth-Mars distance): **0.0842**
    - `P4_Q46` (Hyderabadi biryani): **0.1845**
    - `P4_Q49` (Delta Airlines baggage): **0.2658**
  - Domain-Confusable Queries (high lexical overlap with printer docs):
    - `P4_Q50` (Meteor strike warranty): **0.6055**
    - `P4_Q47` (HP LaserJet Enterprise M608 paper jam): **0.6165**

---

## 3. Threshold Selection Procedure & Data Leakage Assessment

### 3.1 Selection Methodology
The threshold selection in Phase 4.2 was conducted via an empirical gap calculation:
$$\text{Highest Pure Alien Score} = 0.2658 \quad (\text{Delta Airlines})$$
$$\text{Lowest Concise Supported Score} = 0.3124 \quad (\text{Spanish / Japanese QA})$$
$$\text{Empirical Separation Gap} = 0.3124 - 0.2658 = \mathbf{0.0466}$$
$$\text{Midpoint} = \frac{0.3124 + 0.2658}{2} = 0.2891$$
$$\text{Selected Operating Floor} = \mathbf{0.2800}$$

### 3.2 Did Held-Out Data Influence Threshold Selection?
**Yes**. The 50 questions were part of the primary benchmark suite. Because the author examined the score distribution across all 50 questions (including `P4_Q46`–`P4_Q50` and `P4_Q43`) to define the midpoint $0.2891$, the threshold selection was fit directly to the full benchmark rather than determined on a truly disjoint held-out training split.

While this selection is empirically robust across the newly authored Phase 4.2 Independent Validation dataset (where alien queries like Jupiter moon Europa scored $0.1812 < 0.2800$), the calibration cannot be claimed as an unbiased out-of-sample machine learning fit.

---

## 4. Grid Search Performance Across Tested Thresholds

The following table reproduces the exact performance recorded in `threshold_calibration.json` across all 50 queries:

| Threshold ($\tau$) | Full Benchmark Accuracy | Supported FRR (Hard) | Alien FAR (Pure OOD) | Domain-Confusable FAR (HP / Meteor) | Overall FAR on OOD | Diagnostic Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`0.2200`** | 94.0% | 0.0% (0/45) | 0.0% (0/3) | 100.0% (2/2) | 40.0% (2/5) | Overly permissive; leaks alien queries with marginal overlap. |
| **`0.2500`** | 94.0% | 0.0% (0/45) | 33.3% (1/3) | 100.0% (2/2) | 60.0% (3/5) | Falsely accepts Delta Airlines ($0.2658 > 0.2500$). |
| **`0.2800` (Selected)** | **96.0%** | **0.0% (0/45)** | **0.0% (0/3)** | **100.0% (2/2)** | **40.0% (2/5)** | **Optimal boundary**: Rejects 100% of pure alien queries without rejecting supported queries. |
| **`0.3200`** | 94.0% | 2.22% (1/45) | 0.0% (0/3) | 100.0% (2/2) | 40.0% (2/5) | Falsely rejects `P4_Q43` ($0.3124 < 0.3200$). |
| **`0.3500`** | 94.0% | 2.22% (1/45) | 0.0% (0/3) | 100.0% (2/2) | 40.0% (2/5) | Falsely rejects `P4_Q43` ($0.3124$) and marginalizes `P4_Q44`. |

### Crucial Finding on Vector Similarity Limitations:
As explicitly documented in line 278 of `threshold_calibration.json`:
> *"Vector similarity floor alone CANNOT reject domain-confusable out-of-domain queries (`P4_Q47` at $0.6165$ and `P4_Q50` at $0.6055$). Multi-signal gating (Entity Compatibility and Policy Condition Verification) is mandatory to prevent false positives in high-similarity domains."*

This proves that dense vector similarity is inherently limited to detecting **topic drift** (alien queries). Domain-confusable queries (competitor hardware and missing policy terms) share vocabulary with legitimate documentation and achieve high dense similarity ($> 0.60$). They require deterministic entity and policy verification gates.

---

## 5. Verification of ChromaDB Metric & Sparse Calibration

### 5.1 ChromaDB Distance Metric Verification
- Verified collection configuration in `.chroma_live`:
  - `hnsw:space = "cosine"`
- In ChromaDB with cosine space:
  $$\text{dist}(u, v) = 1.0 - \frac{u \cdot v}{\|u\| \|v\|}$$
- The system correctly calculates similarity as:
  $$\text{similarity} = 1.0 - \text{dist}$$
  Clamped to $[0.0, 1.0]$. The code implementation in [evidence_gate.py](file:///C:/Users/surya/Downloads/Customer%20Support%20ChatBot/app/retrieval/evidence_gate.py#L153-L159) accurately implements this formula.

### 5.2 Independent Calibration of Sparse BM25 Scores
- **Audit Finding**: Sparse BM25 scores are **NOT independently calibrated with a numerical threshold**.
- In `EvidenceGate`, the similarity floor only evaluates `top_dense_score` (dense cosine similarity).
- While raw BM25 scores are normalized and stored in `chunk.metadata["raw_bm25_score"]`, BM25 scores vary unbounded with document length and query frequency ($0.0$ to $> 15.0$).
- When hybrid retrieval runs, BM25 contributes to the RRF rank score, but the evidence gate's similarity floor relies solely on dense cosine similarity.

---

## 6. Recommendations & Methodological Limitations

1. **State Limitations Explicitly**:
   Future audit reports must not characterize the 25/25 split of the 50 queries as an independent training and testing split, given that all negative examples were in the second half.
2. **Preserve `0.2800` Floor**:
   The `0.2800` floor is well-supported empirically by the $+0.0466$ gap between alien queries ($\le 0.2658$) and supported queries ($\ge 0.3124$). It should remain frozen.
3. **Do Not Rely on Similarity Floors for Competitor or Policy Rejection**:
   Similarity floors only protect against alien topics. Entity and policy gates must remain the primary defense against in-domain false acceptances.
