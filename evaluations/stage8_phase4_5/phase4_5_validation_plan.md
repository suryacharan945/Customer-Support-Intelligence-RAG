# Stage 8 Phase 4.5: Independent Validation, Human Review & Release Readiness Audit Plan

**Document Version**: 1.0  
**Phase**: Stage 8 Phase 4.5  
**Active Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Branch**: `master`  
**Frozen Baseline Commit**: `534f279`  
**Parent Commit**: `dc1b555`  
**Execution Date**: 2026-11-15  

---

## 1. Objectives & Validation Scope

Stage 8 Phase 4.5 is a rigorous, independent quality assurance and release readiness validation milestone. Following the Phase 4.4 implementation of compound query decomposition and claim-level evidence coverage, Phase 4.5 establishes whether the system is truly robust, generalizable, reproducible, and ready for release without superficial metric inflation.

### Key Validation Objectives:
1. **Freeze Implementation Baseline**: Snapshot Phase 4.4 code and benchmark datasets with cryptographic SHA256 hashes to guarantee that all downstream evaluations occur against the untouched, frozen implementation.
2. **Reconcile Historical Benchmarks**: Perform raw per-query reconciliation across all 112 historical queries (Phase 4: 50, Phase 4.1: 10, Phase 4.2: 32, Phase 4.4: 20), computing 12 distinct mathematical metrics without conflating citation validity with semantic support.
3. **Execute Blind Compound-Query Benchmark**: Author and evaluate a completely new, independently designed 30-query test set covering 15 distinct structural and semantic challenge categories without modifying or tuning the pipeline.
4. **Audit Decomposition Quality**: Quantify sub-question precision, recall, exact decomposition match, clause omission rate, unnecessary decomposition rate, and anaphora resolution accuracy.
5. **Audit Claim-Level Provenance & Grounding**: Trace sub-questions to supporting chunk IDs, validating that claims are strictly grounded in retrieved evidence.
6. **Deploy Human Review Template**: Provide a standardized human review template (`human_review_phase4_5.csv`) for raters and explicitly disclose evaluation completion status without fabricating ratings.
7. **Adversarial & Failure Case Stress-Testing**: Probe boundary conditions, including prompt injections, non-existent attributes, unit mismatches, negation, and cross-domain comparisons.
8. **Pipeline Latency & Execution-Path Audit**: Benchmark end-to-end and component latency across cold-start vs. warm execution and all four evidence statuses (`SUFFICIENT`, `PARTIAL`, `INSUFFICIENT`, `CONFLICTING`).
9. **Final Release Verdict**: Issue an evidence-grounded `GO`, `CONDITIONAL GO`, or `NO-GO` recommendation for Stage 9.

---

## 2. Safety & Workspace Constraints

- **Active Workspace**: `C:\Users\surya\Downloads\Customer Support ChatBot` on `master`.
- **Alternate Workspace**: `C:\Users\surya\Internship_RAG_MCP_Capstone` must remain completely untouched.
- **Local Storage Constraint**: Local tracked footprint must remain strictly below 1,024 MB (baseline is 3.65 MiB). Hard stop above 2,048 MB.
- **Zero-Cost / Secret Safety**: No external model downloads, no paid API calls, no Docker daemon builds, and zero secrets in source code or archives.
- **Backup Strategy**: Timestamped source code and ChromaDB snapshots committed to Google Drive (`G:\My Drive\Internship_RAG_MCP_Capstone`) with SQLite integrity verification.

---

## 3. Metric Definitions & Calculation Standards

To eliminate ambiguity and prevent arithmetic inflation, metrics are reported independently according to the following formulas:

1. **Four-Class Overall Accuracy**:
   $$\text{Accuracy}_{\text{4-class}} = \frac{\sum_{i=1}^{N} \mathbb{I}(\hat{y}_i = y_i)}{N}$$
   Where $y_i, \hat{y}_i \in \{\text{SUFFICIENT}, \text{PARTIAL}, \text{INSUFFICIENT}, \text{CONFLICTING}\}$.

2. **Per-Class Precision & Recall**:
   $$\text{Precision}_c = \frac{TP_c}{TP_c + FP_c}, \quad \text{Recall}_c = \frac{TP_c}{TP_c + FN_c}$$
   Reported separately for each of the 4 evidence classes.

3. **False Acceptance Rate (FAR)**:
   Proportion of unsupported, alien, or partial queries erroneously classified as `SUFFICIENT`:
   $$\text{FAR} = \frac{\text{False Positives (Predicted SUFFICIENT when expected } \ne \text{SUFFICIENT)}}{\text{Total Non-SUFFICIENT Queries}}$$

4. **False Rejection Rate (FRR)**:
   Proportion of valid, fully supported queries erroneously classified as `INSUFFICIENT`, `PARTIAL`, or `CONFLICTING`:
   $$\text{FRR} = \frac{\text{False Negatives (Predicted non-SUFFICIENT when expected } = \text{SUFFICIENT)}}{\text{Total SUFFICIENT Queries}}$$

5. **Compound-Query Exact Match (CEM)**:
   Proportion of compound inquiries where the full set of decomposed sub-questions and overall status match ground truth:
   $$\text{CEM} = \frac{\sum \mathbb{I}(\hat{S}_i = S_i \land \hat{y}_i = y_i)}{N_{\text{compound}}}$$

6. **Sub-Question Decomposition Precision & Recall**:
   - $\text{Precision}_{\text{sq}} = \frac{|\text{Correctly Decomposed Sub-Questions}|}{|\text{Total Generated Sub-Questions}|}$
   - $\text{Recall}_{\text{sq}} = \frac{|\text{Correctly Identified Sub-Questions}|}{|\text{Total Ground-Truth Sub-Questions}|}$

7. **Clause Omission Rate (COR) & Unnecessary Decomposition Rate (UDR)**:
   - $\text{COR} = \frac{\text{Omitted Sub-Questions}}{\text{Total Ground-Truth Sub-Questions}}$
   - $\text{UDR} = \frac{\text{Spuriously Invented Sub-Questions}}{\text{Total Generated Sub-Questions}}$

8. **Anaphora Resolution Accuracy**:
   $$\text{Acc}_{\text{anaphora}} = \frac{\text{Correctly Resolved Entity References}}{\text{Total Sub-Questions Containing Pronouns / Relative References}}$$

9. **Claim-Level Evidence Support Rate**:
   $$\text{Support Rate} = \frac{\text{Grounded Assertions with Verifiable Passage Support}}{\text{Total Synthesized Assertions}}$$

10. **Citation Coverage & Source Integrity**:
    - Citation Coverage: Proportion of factual assertions carrying an immediate bracketed citation.
    - Citation Source Integrity: Proportion of bracketed citations matching actual indexed chunk IDs and filenames.

---

## 4. Benchmark Reconciliation Methodology

The historical benchmark audit systematically inspects every query across:
1. **Phase 4 Original Benchmark** (50 questions): Reconciles the historical 42/50 result, distinguishing pure in-domain answer generation accuracy (42/45 = 93.3%) from strict 4-class taxonomy accuracy (42/50 = 84.0%), documenting the status of Category G partial queries.
2. **Phase 4.1 Regression Benchmark** (10 questions): Confirms the 10/10 consistency on targeted alien and policy inquiries.
3. **Phase 4.2 Independent Validation Benchmark** (32 questions): Re-evaluates all 32 questions, specifically verifying that `P4_2_VAL23` evaluates to `PARTIAL` (0% false acceptance) and documenting the behavior of `VAL21` and `VAL22`.
4. **Phase 4.4 Compound Benchmark** (20 questions): Audits the 20/20 result across the 5 structural categories.
5. **Combined Reconciliation Table**: Generates a unified JSON and Markdown artifact recording original vs. audited labels with explicit written rationales.

---

## 5. Blind Compound-Query Protocol

A new 30-query benchmark dataset (`evaluations/stage8_phase4_5/blind_compound_query_dataset.json`) is designed completely independently of the implementation's hardcoded patterns:
- 15 distinct scenario categories (two supported clauses, one missing clause, three clauses mixed, cross-product comparisons, cross-domain comparisons, conditional action-consequence, negation and exceptions, ambiguous pronouns, missing commercial pricing, missing policy details, conflicting document versions, similar entities with different specs, unanswering related passages, high lexical overlap alien inquiries, and prompt injection attempts).
- Each record includes ground-truth sub-questions, expected claims, answerability, expected evidence status, and relevant document IDs.
- Execution occurs without modifying or tuning the pipeline code, establishing true blind evaluation validity.

---

## 6. Execution Roadmap & Deliverables

| Step | Output Artifact | Description |
|:---:|:---|:---|
| **1** | `phase4_5_validation_plan.md` | This formal validation plan. |
| **2** | `phase4_5_baseline_manifest.json` | Frozen implementation and dataset hashes. |
| **3** | `benchmark_reconciliation.json` | Raw per-query reconciliation data across 112 queries. |
| **4** | `benchmark_reconciliation_report.md` | Formal mathematical reconciliation and discrepancy report. |
| **5** | `blind_compound_query_dataset.json` | 30 independently authored blind evaluation questions. |
| **6** | `blind_compound_query_results.json` | Execution results and traces on the blind benchmark. |
| **7** | `decomposition_metrics.json` | Precision, recall, omission, and anaphora metrics. |
| **8** | `claim_grounding_audit.json` | Provenance traceability from claims to chunk IDs. |
| **9** | `human_review_phase4_5.csv` | Standardized human review rater template. |
| **10** | `adversarial_test_results.json` | Boundary and security stress-test results. |
| **11** | `latency_profile.json` | Multi-path latency distribution and component timings. |
| **12** | `regression_comparison.json` | Side-by-side performance comparison against frozen baseline. |
| **13** | `evaluation_report_phase4_5.md` | Comprehensive final report with release readiness verdict. |
| **14** | Drive Backup & Standalone ZIP | Verified cloud snapshot and standalone archive. |
