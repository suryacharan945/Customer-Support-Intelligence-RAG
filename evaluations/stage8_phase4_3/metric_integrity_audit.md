# Stage 8 Phase 4.3: Metric Integrity & Evaluation Arithmetic Audit

**Target Document Audited**: `evaluations/stage8_phase4_2/evaluation_report_phase4_2.md`  
**Raw Source Files Audited**:
- `evaluations/stage8_phase4_2/original_benchmark_results.json` (50 queries)
- `evaluations/stage8_phase4_2/regression_benchmark_results.json` (10 queries)
- `evaluations/stage8_phase4_2/independent_validation_results.json` (32 queries)
- `evaluations/stage8_phase4_2/independent_validation_dataset.json` (32 queries)  
**Date**: November 15, 2026  
**Auditor**: Evaluation Integrity & Independent Verification Engine  

---

## 1. Executive Summary of Discrepancies

A comprehensive mathematical audit of the Phase 4.2 evaluation report (`evaluation_report_phase4_2.md`) and the underlying raw query-level execution logs revealed three distinct reporting discrepancies and identified inconsistent metric definitions between the evaluation runner script (`run_stage8_phase4_2_evaluations.py`) and the prose summary tables.

All historical raw execution files remain completely intact and immutable. This audit documents the exact mathematical causes of the drift and establishes the corrected, unambiguous benchmark figures.

| Benchmark Suite | Reported Accuracy | Exact Recomputed Accuracy | Reported Supported Success | Actual Supported Success (`act == SUFFICIENT`) | Reported FRR | Recomputed FRR (Hard Abstention) | Recomputed FRR (Strict Classification) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Original Phase 4 (50 Qs)** | 84.0% | **84.00%** (42/50) | 37/45 (82.2%) | **42/45 (93.33%)** | 2.2% | **2.22%** (1/45) | **17.78%** (8/45) |
| **Phase 4.1 Regression (10 Qs)** | 100.0% | **100.00%** (10/10) | 5/5 (100.0%) | **5/5 (100.00%)** | 0.0% | **0.00%** (0/5) | **0.00%** (0/5) |
| **Independent Validation (32 Qs)** | 84.4% | **84.38%** (27/32) | 19/20 (95.0%) | **19/20 (95.00%)** | 0.0% | **0.00%** (0/20) | **5.00%** (1/20) |
| **Combined Master Suite (92 Qs)** | **86.9%** | **85.87%** (79/92) | 61/70 (87.1%) | **66/70 (94.29%)** | 1.4% | **1.43%** (1/70) | **12.86%** (9/70) |

---

## 2. Investigation of Specific Discrepancies

### 2.1 Discrepancy A: Original Benchmark Supported Success (37/45) vs. False Rejection Rate (2.2%)

#### The Reported Discrepancy
In the Phase 4.2 executive summary table:
- Supported Success Rate: **37/45 (82.2%)**
- False Rejection Rate (FRR): **2.2%**

Mathematically, if 37 out of 45 supported questions succeeded, then 8 questions did not succeed. An error rate of $\frac{8}{45} = 17.78\%$, which conflicts with the reported $2.2\%$.

#### Root Cause Analysis
This discrepancy arose from a divergence between two different definitions of "failure" and a category labeling mismatch in the 50-question benchmark:

1. **How 37 was computed**:
   In `run_stage8_phase4_2_evaluations.py`, the variable `correct_sufficient_count` tracks queries where `expected_status == "SUFFICIENT"` AND `actual_status == "SUFFICIENT"`.
   In the original benchmark of 50 queries:
   - 40 queries had `expected_status == "SUFFICIENT"`.
   - 5 queries had `expected_status == "PARTIAL"` (Category G: Ambiguous / Partial queries `P4_Q41` through `P4_Q45`).
   - 5 queries had `expected_status == "INSUFFICIENT"` (Category H: Out-of-Domain queries `P4_Q46` through `P4_Q50`).
   Out of the 40 queries expected to be `SUFFICIENT`, exactly **37** were classified as `SUFFICIENT`.
   However, the denominator used in prose was the total supported query count ($40 + 5 = 45$).
   Comparing 37 (the numerator of the 40 expected-SUFFICIENT queries) against 45 (which includes the 5 expected-PARTIAL queries) produced $\frac{37}{45} = 82.2\%$.
   In reality, all 5 expected-PARTIAL queries were answered by the system as `SUFFICIENT`. Thus, the actual number of supported queries answered as `SUFFICIENT` was $37 + 5 = \mathbf{42/45}$ ($93.33\%$).

2. **How 2.2% was computed**:
   In `run_stage8_phase4_2_evaluations.py` (line 164), the runner script implemented the following logic for false rejection:
   ```python
   if is_supp:
       supported_total += 1
       if act == "INSUFFICIENT":
           false_rejections += 1
   ```
   The runner defined a "False Rejection" strictly as **Hard Abstention on Supported Evidence** (`actual_status == "INSUFFICIENT"`).
   Among the 45 supported queries, exactly **one** query was classified as `INSUFFICIENT` (`P4_Q09`, Error E-101 Printhead Jam):
   $$\text{FRR}_{\text{hard}} = \frac{1}{45} = 0.02222... \approx \mathbf{2.22\%}$$
   The remaining 7 non-matching queries were:
   - 1 query classified as `PARTIAL` (`P4_Q28`, Fuser thermal fuse threshold).
   - 1 query classified as `CONFLICTING` (`P4_Q18`, Error E-204 fuser disassembly under warranty).
   - 5 queries where `expected_status == "PARTIAL"` were classified as `SUFFICIENT` (`P4_Q41` to `P4_Q45`).

#### Reconciliation
- **Hard Abstention FRR** (`act == INSUFFICIENT` on supported): **1 / 45 = 2.22%**.
- **Strict Classification FRR** (`act != expected_status` on supported): **8 / 45 = 17.78%**.
- **Supported Answerability Rate** (`act == SUFFICIENT` on supported): **42 / 45 = 93.33%**.

---

### 2.2 Discrepancy B: Combined Benchmark Supported Success (61/70) vs. False Rejection Rate (1.4%)

#### The Reported Discrepancy
In the Phase 4.2 executive summary table:
- Combined Supported Success Rate: **61/70 (87.1%)**
- Combined False Rejection Rate: **1.4%**

If 61 of 70 succeeded, then $70 - 61 = 9$ queries did not succeed. $\frac{9}{70} = 12.86\%$, which conflicts with the reported $1.4\%$.

#### Root Cause Analysis
The combined supported count was obtained by summing `correct_sufficient_count` across the three benchmarks:
$$\text{Original } (37) + \text{Regression } (5) + \text{Validation } (19) = \mathbf{61}$$
Total supported queries across the three benchmarks:
$$\text{Original } (45) + \text{Regression } (5) + \text{Validation } (20) = \mathbf{70}$$
Comparing $61 / 70 = 87.14\%$ again used `correct_sufficient_count` in the numerator while using total supported queries in the denominator.

Meanwhile, the reported FRR ($1.4\%$) was computed using the runner script's hard-abstention formula across all 70 supported queries:
Only **one** supported query across all 70 supported queries was classified as `INSUFFICIENT` (`P4_Q09`):
$$\text{FRR}_{\text{hard, combined}} = \frac{1}{70} = 0.0142857... \approx \mathbf{1.43\%}$$

The 9 supported queries that did not have `expected == actual == SUFFICIENT` were:
- 1 hard abstention: `P4_Q09` (`act == INSUFFICIENT`).
- 2 conflicting classifications: `P4_Q18` and `P4_2_VAL06` (`act == CONFLICTING`).
- 1 partial classification: `P4_Q28` (`act == PARTIAL`).
- 5 partial queries over-accepted as sufficient: `P4_Q41` through `P4_Q45` (`exp == PARTIAL, act == SUFFICIENT`).

#### Reconciliation
- **Combined Hard Abstention FRR** (`act == INSUFFICIENT` on supported): **1 / 70 = 1.43%**.
- **Combined Non-Sufficient Rate** (`act != SUFFICIENT` on supported): **4 / 70 = 5.71%** (queries: `P4_Q09`, `P4_Q18`, `P4_Q28`, `P4_2_VAL06`).
- **Combined Strict Classification Error** (`act != expected` on supported): **9 / 70 = 12.86%**.
- **Combined Supported Answerability Rate** (`act == SUFFICIENT` on supported): **66 / 70 = 94.29%**.

---

### 2.3 Discrepancy C: Combined Benchmark Accuracy (Reported 86.9% vs. Exact 85.87%)

#### The Reported Discrepancy
The executive summary table in `evaluation_report_phase4_2.md` reported:
- Combined Benchmark Accuracy: **86.9%**

#### Exact Recomputed Arithmetic
From individual query verdicts (`verdict == "PASS"`, meaning `actual_status == expected_status`):
- **Original Phase 4**: 42 PASS / 50 total ($84.00\%$)
- **Phase 4.1 Regression**: 10 PASS / 10 total ($100.00\%$)
- **Phase 4.2 Independent Validation**: 27 PASS / 32 total ($84.375\%$)

Aggregating the raw counts:
$$\text{Total Passed} = 42 + 10 + 27 = \mathbf{79}$$
$$\text{Total Evaluated} = 50 + 10 + 32 = \mathbf{92}$$
$$\text{Exact Combined Accuracy} = \frac{79}{92} = 0.85869565... \approx \mathbf{85.87\%}$$

#### Source of Error
The reported figure of $86.9\%$ was a transcription/calculation error. The unweighted arithmetic mean of the three percentage figures is:
$$\frac{84.0\% + 100.0\% + 84.38\%}{3} = \frac{268.38\%}{3} = 89.46\%$$
The true weighted accuracy is strictly $\frac{79}{92} = \mathbf{85.87\%}$.

---

## 3. Comprehensive Verification of Totals & Confusion Matrices

Auditing the individual query records confirmed that all query IDs, counts, category assignments, and confusion matrix cell sums agree with mathematical precision:

### 3.1 Original Phase 4 Benchmark (50 Queries)
- **Total**: 50 queries.
- **Expected Status Distribution**:
  - `SUFFICIENT`: 40
  - `PARTIAL`: 5
  - `INSUFFICIENT`: 5
- **Actual Status Distribution**:
  - `SUFFICIENT`: 42
  - `INSUFFICIENT`: 6
  - `CONFLICTING`: 1
  - `PARTIAL`: 1
- **Confusion Matrix Verification**:
  - Row `SUFFICIENT`: $37 + 1 + 1 + 1 = 40$ (Matches expected 40).
  - Row `PARTIAL`: $5 + 0 + 0 + 0 = 5$ (Matches expected 5).
  - Row `INSUFFICIENT`: $0 + 0 + 5 + 0 = 5$ (Matches expected 5).
  - Column `SUFFICIENT`: $37 + 5 + 0 + 0 = 42$ (Matches actual 42).
  - Column `PARTIAL`: $1 + 0 + 0 + 0 = 1$ (Matches actual 1).
  - Column `INSUFFICIENT`: $1 + 0 + 5 + 0 = 6$ (Matches actual 6).
  - Column `CONFLICTING`: $1 + 0 + 0 + 0 = 1$ (Matches actual 1).

### 3.2 Phase 4.1 Regression Benchmark (10 Queries)
- **Total**: 10 queries.
- **Expected Status Distribution**: `SUFFICIENT`: 5, `INSUFFICIENT`: 5.
- **Actual Status Distribution**: `SUFFICIENT`: 5, `INSUFFICIENT`: 5.
- **Confusion Matrix Verification**:
  - Row `SUFFICIENT`: $5 + 0 + 0 + 0 = 5$.
  - Row `INSUFFICIENT`: $0 + 0 + 5 + 0 = 5$.
  - Total exact diagonal matches: 10/10 ($100.0\%$).

### 3.3 Phase 4.2 Independent Validation Benchmark (32 Queries)
- **Total**: 32 queries.
- **Expected Status Distribution**:
  - `SUFFICIENT`: 20
  - `INSUFFICIENT`: 9
  - `CONFLICTING`: 2
  - `PARTIAL`: 1
- **Actual Status Distribution**:
  - `SUFFICIENT`: 23
  - `INSUFFICIENT`: 8
  - `CONFLICTING`: 1
- **Confusion Matrix Verification**:
  - Row `SUFFICIENT`: $19 + 0 + 0 + 1 = 20$ (Matches expected 20).
  - Row `PARTIAL`: $1 + 0 + 0 + 0 = 1$ (Matches expected 1).
  - Row `INSUFFICIENT`: $1 + 0 + 8 + 0 = 9$ (Matches expected 9).
  - Row `CONFLICTING`: $2 + 0 + 0 + 0 = 2$ (Matches expected 2).
  - Column `SUFFICIENT`: $19 + 1 + 1 + 2 = 23$ (Matches actual 23).
  - Column `INSUFFICIENT`: $0 + 0 + 8 + 0 = 8$ (Matches actual 8).
  - Column `CONFLICTING`: $1 + 0 + 0 + 0 = 1$ (Matches actual 1).

---

## 4. Standardized Metric Definitions for Future Evaluations

To prevent ambiguous reporting, the following standardized definitions are established and enforced across all project artifacts:

1. **Exact Classification Accuracy**:
   $$\text{Accuracy} = \frac{\sum_{i=1}^N \mathbb{I}(\text{actual}_i = \text{expected}_i)}{N}$$

2. **False Acceptance Rate on Unsupported / OOD (FAR)**:
   $$\text{FAR} = \frac{\text{Count}(\text{is\_supported} = \text{False} \land \text{actual} = \text{'SUFFICIENT'})}{\text{Count}(\text{is\_supported} = \text{False})}$$

3. **Appropriate Abstention Rate on Unsupported / OOD (AAR)**:
   $$\text{AAR} = 1.0 - \text{FAR} = \frac{\text{Count}(\text{is\_supported} = \text{False} \land \text{actual} \in \{\text{'INSUFFICIENT'}, \text{'CONFLICTING'}\})}{\text{Count}(\text{is\_supported} = \text{False})}$$

4. **Hard Abstention False Rejection Rate ($\text{FRR}_{\text{hard}}$)**:
   $$\text{FRR}_{\text{hard}} = \frac{\text{Count}(\text{is\_supported} = \text{True} \land \text{actual} = \text{'INSUFFICIENT'})}{\text{Count}(\text{is\_supported} = \text{True})}$$

5. **Supported Answerability Rate (SAR)**:
   $$\text{SAR} = \frac{\text{Count}(\text{is\_supported} = \text{True} \land \text{actual} = \text{'SUFFICIENT'})}{\text{Count}(\text{is\_supported} = \text{True})}$$

6. **Strict Classification Error on Supported ($\text{FRR}_{\text{strict}}$)**:
   $$\text{FRR}_{\text{strict}} = \frac{\text{Count}(\text{is\_supported} = \text{True} \land \text{actual} \ne \text{expected})}{\text{Count}(\text{is\_supported} = \text{True})}$$
