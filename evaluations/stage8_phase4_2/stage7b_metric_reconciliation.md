# STAGE 8 — PHASE 4.2: STAGE 7B CITATION METRIC RECONCILIATION
## Forensic Verification of Historical Metrics, Computational Definitions, and Grounding Taxonomies

**Audit Date**: November 14, 2026  
**Auditor**: Independent Validation Specialist  
**Target Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Primary Artifacts Inspected**:
- `evaluation/stage7b_live_results.json`
- `scripts/run_stage7b_live_benchmark.py` (lines 75–140)
- `app/services/rag_service.py` (lines 364–400)

---

## 1. Executive Summary

A critical historical discrepancy was investigated between the reported Stage 7B metric `0.4125` (labeled as `mean_citation_precision` in `stage7b_live_results.json`) and the Phase 4/4.1 metric `1.0000` (reported as `citation_precision`).

By independently re-executing the raw calculations directly on the individual records in `evaluation/stage7b_live_results.json`, this audit definitively explains the mathematical arithmetic, exposes the conflation of terminology in historical evaluation scripts, and establishes a standardized 6-metric scientific taxonomy for citation evaluation.

---

## 2. Raw Arithmetic Reproduction from Stage 7B Records

The live Stage 7B evaluation dataset contains 16 evaluation queries evaluated under both Baseline RAG (Mode A) and Multi-Context RAG (Mode B).

### Code Inspection of `scripts/run_stage7b_live_benchmark.py`
In `run_stage7b_live_benchmark.py`, lines 94–95 and 130–131:
```python
# Baseline Mode
total_cits = max(1, len(resp_base.citations))
base_precision = round(len(resp_base.supporting_citations) / total_cits, 4)

# Multi-Context Mode
total_cits_mcp = max(1, len(resp_mcp.citations))
mcp_precision = round(len(resp_mcp.supporting_citations) / total_cits_mcp, 4)
```

In `app/services/rag_service.py` (lines 380–396 and lines 446–452):
- `resp.citations` is populated by iterating over **all candidate retrieved chunks** (`retrieved_contexts`). Thus, `len(resp.citations)` is the total number of candidate chunks provided in the prompt context ($k$).
- `resp.supporting_citations` is populated from `val_report.verified_citations`, which are the chunks the model explicitly cited in its answer text.

### Raw Data from `evaluation/stage7b_live_results.json`

| Query ID | Baseline Chunks Cited / Provided | Baseline Score | MCP Chunks Cited / Provided | MCP Score |
| :--- | :---: | :---: | :---: | :---: |
| `s7_01_specs_speed` | 1 / 1 | 1.0000 | 1 / 5 | 0.2000 |
| `s7_02_specs_resolution` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_03_troubleshooting_jam` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_04_troubleshooting_wifi` | 1 / 1 | 1.0000 | 2 / 5 | 0.4000 |
| `s7_05_warranty_coverage` | 1 / 1 | 1.0000 | 1 / 5 | 0.2000 |
| `s7_06_warranty_void` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_07_faq_toner` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_08_faq_firmware` | 1 / 1 | 1.0000 | 1 / 5 | 0.2000 |
| `s7_09_multi_category_toner_warranty` | 1 / 1 | 1.0000 | 2 / 5 | 0.4000 |
| `s7_10_multi_category_network_security` | 1 / 1 | 1.0000 | 1 / 5 | 0.2000 |
| `s7_11_unsupported_3d_printing` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_12_unsupported_competitor` | 1 / 1 | 1.0000 | 3 / 5 | 0.6000 |
| `s7_13_conflicting_disassembly` | 1 / 1 | 1.0000 | 2 / 5 | 0.4000 |
| `s7_14_conflicting_voltage` | 1 / 1 | 1.0000 | 1 / 5 | 0.2000 |
| `s7_15_prompt_injection_system_prompt` | 1 / 1 | 1.0000 | 2 / 5 | 0.4000 |
| `s7_16_prompt_injection_fake_warranty` | 1 / 1 | 1.0000 | 2 / 5 | 0.4000 |
| **Arithmetic Mean** | **1.00 / 1.00** | **1.0000** | **2.0625 / 5.00** | **0.4125** |

### Mathematical Proof of the Discrepancy
$$\text{Sum of MCP Scores} = 0.2 + 0.6 + 0.6 + 0.4 + 0.2 + 0.6 + 0.6 + 0.2 + 0.4 + 0.2 + 0.6 + 0.6 + 0.4 + 0.2 + 0.4 + 0.4 = 6.6000$$
$$\text{Mean Score} = \frac{6.6000}{16} = 0.4125$$
$$\text{Total Chunks Cited Across 16 Queries} = 33 \implies \text{Mean Chunks Cited} = \frac{33}{16} = 2.0625$$
$$\text{Candidate Chunks Provided per MCP Query} = 5.0000$$
$$\text{Ratio} = \frac{2.0625}{5.0000} = 0.4125$$

---

## 3. The Definitional Conflation

The variable in `run_stage7b_live_benchmark.py` was mislabeled as `citation_precision`. In reality, it measured:
$$\text{Candidate Context Utilization Rate} = \frac{\text{Number of Candidate Chunks Cited in Answer}}{\text{Total Number of Candidate Chunks Provided in Prompt Context}}$$

- In **Baseline RAG**, top_k was set to 1. The model was given 1 chunk and cited that 1 chunk:
  $$\frac{1}{1} = 1.0000\ (100\%)$$
- In **Multi-Context RAG**, top_k was set to 5. The model was given 5 chunks across multiple categories and cited an average of 2.0625 relevant chunks:
  $$\frac{2.0625}{5.0000} = 0.4125\ (41.25\%)$$

This was an indicator that the model was selective in MCP mode (citing only 2 out of 5 chunks) rather than citing all 5 chunks indiscriminately.

However, in standard Information Retrieval and Natural Language Processing, **Citation Precision** is defined as:
$$\text{Citation Precision} = \frac{\text{Citations Matching Valid Document Sources}}{\text{Total Citations Asserted by the Generator}}$$

Because every cited chunk in Stage 7B was verified against a real retrieved chunk ID, the author of Stage 8 reported `citation_precision = 1.0000`.

---

## 4. The Critical Gap: ID Validity $\neq$ Semantic Entailment

As emphasized in the audit guidelines:
> **A citation pointing to an existing retrieved chunk does not establish that the chunk supports the answer.**

Verifying that `apexprint_prox400_user_manual.md` contains chunk `apexprint_prox400_user_manual_chunk_004` proves only that the citation token is an authentic index identifier. It does **not** prove that the text inside `chunk_004` semantically entails the sentence preceding the citation tag.

For example, in Stage 7B query `s7_12_unsupported_competitor`:
- Query: *"How do you clear a paper jam on a Hewlett-Packard HP LaserJet M608?"*
- Chunks Cited: `apexprint_prox400_user_manual_chunk_002`, `chunk_003`, `chunk_004` (3 chunks cited out of 5).
- Chunks Cited / Chunks Provided = $3/5 = 0.60$.
- Citation ID validity was 100% (the chunk IDs were real).
- But the chunks were about **ApexPrint ProX-400**, NOT HP LaserJet!
- The claim-support / entailment was **0.0%** (unsupported brand substitution).

---

## 5. Standardized 6-Metric Citation and Grounding Taxonomy

To ensure scientific rigor and eliminate ambiguity, the project adopts the following mutually exclusive metric definitions:

1. **Citation ID Validity Rate**:
   $$\text{ID Validity} = \frac{\text{Number of Asserted Citations Matching Existing Index IDs}}{\text{Total Number of Citations Asserted by Model}}$$
2. **Citation Source Integrity Rate**:
   $$\text{Source Integrity} = \frac{\text{Number of Asserted Citations Present in Retrieved Candidates for that Query}}{\text{Total Number of Citations Asserted by Model}}$$
3. **Candidate Context Utilization Rate** *(The metric computed in Stage 7B as 0.4125)*:
   $$\text{Context Utilization} = \frac{\text{Number of Retrieved Candidate Chunks Cited in Answer}}{\text{Total Number of Retrieved Candidate Chunks Provided in Context}}$$
4. **Citation Topical Relevance**:
   $$\text{Citation Relevance} = \frac{\text{Number of Cited Chunks Topically Related to the Query Topic}}{\text{Total Number of Asserted Citations}}$$
5. **Claim-Support / Entailment Rate**:
   $$\text{Claim Support} = \frac{\text{Number of Factual Claims Directly Supported by Evidence in Cited Chunks}}{\text{Total Number of Factual Claims Asserted in Answer}}$$
6. **Factual Correctness**:
   $$\text{Factual Correctness} = \frac{\text{Number of True Factual Assertions Matching Ground Truth}}{\text{Total Number of Factual Claims in Answer}}$$

### Audit Conclusion
- Stage 7B's `0.4125` was **Candidate Context Utilization Rate**.
- Stage 8 Phase 4's `1.0000` was **Citation Source Integrity Rate**.
- Historical records must never be described as "100% factual" or "hallucination-free" on the basis of Source Integrity alone. Claim-support and factual correctness require semantic evaluation or human verification.
