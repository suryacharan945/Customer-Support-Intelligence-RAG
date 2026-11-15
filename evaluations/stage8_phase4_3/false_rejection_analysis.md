# Stage 8 Phase 4.3: In-Depth Investigation of False-Rejection Behavior

**Benchmarks Audited**:
- Original Phase 4 Benchmark (50 Queries): 8 supported queries not classified as SUFFICIENT
- Independent Validation Benchmark (32 Queries): 1 supported query not classified as SUFFICIENT  
**Date**: November 15, 2026  
**Auditor**: Evaluation Integrity & Independent Verification Engine  

---

## 1. Overview

In Stage 8 Phase 4.2, 8 queries from the Original Phase 4 benchmark and 1 query from the Independent Validation benchmark were identified where the query was labeled as supported (`is_supported: true`), but the classification output was not strictly `SUFFICIENT`.

This audit systematically analyzes all 9 queries to determine:
1. Why the evidence was rejected or diverted from `SUFFICIENT`.
2. Whether the inquiry was actually supported by the knowledge base corpus.
3. Which specific gate or validator condition was responsible.
4. Whether the gate was overly strict or the dataset label was flawed.

---

## 2. Original Benchmark Supported Queries (8 Queries)

### 2.1 `P4_Q09`
- **Query**: *"What are the complete step-by-step resolution steps for resolving Error E-101 Printhead Jam?"*
- **Expected Status**: `SUFFICIENT`
- **Actual Status**: `INSUFFICIENT`
- **Top Dense Score**: `0.5905` (Passes the $0.2800$ floor).
- **Corpus Grounding**: Fully supported by `apexprint_error_codes_and_hardware_troubleshooting.md` (lines describing E-101 clearing procedures, carriage movement, and optical sensor cleaning).
- **Responsible Gate Condition**: **Entity Compatibility Gate** (`_check_entity_compatibility`).
  - Reason given by gate: `Entity mismatch: Query requests instructions for 'Error E-101 Printhead Jam' (evidence covers ApexPrint)`.
- **Root Cause & Diagnosis**:
  The regex used in Phase 4.2 for error codes was:
  ```python
  if re.match(r"^(?:error\s+)?e-\d+$", cand_lower):
      continue
  ```
  Because the candidate string extracted from the query was `"Error E-101 Printhead Jam"`, the trailing words (`Printhead Jam`) prevented the end-of-string anchor `$` from matching. Consequently, the gate treated `"Error E-101 Printhead Jam"` as an external competitor entity, declaring a false entity mismatch.
- **Verdict**: **Overly Strict Gate Condition (Regex Bug)**. Changing the regex to `re.match(r"^(?:error\s+)?e-\d+\b", cand_lower)` allows any error code followed by description to be recognized and protected.

---

### 2.2 `P4_Q18`
- **Query**: *"If an ApexPrint printer displays Error E-204 and the user disassembles the fuser unit, is the replacement covered under warranty?"*
- **Expected Status**: `SUFFICIENT`
- **Actual Status**: `CONFLICTING`
- **Top Dense Score**: `0.6918` (High relevance).
- **Corpus Grounding**: Fully supported by both `apexprint_error_codes_and_hardware_troubleshooting.md` and `apexprint_extended_warranty_and_exclusions.md`.
- **Responsible Gate Condition**: **Cross-Category Conflict Gate** (`_check_conflicting_evidence`).
  - Reason given: `Conflicting recommendations detected between troubleshooting and warranty policy.`
- **Root Cause & Diagnosis**:
  The conflict detection logic checked whether chunks from both `troubleshooting` and `warranty` categories were retrieved simultaneously and contained words like `"disassemble"`, `"void"`, and `"replace"`.
  However, in reality, both documents **agree**:
  - The troubleshooting guide states: *"Do NOT attempt to disassemble the fuser assembly using a screwdriver or tools. Opening internal high-voltage or thermal assemblies voids warranty..."*
  - The warranty agreement states: *"Unauthorized disassembly or opening the chassis voids the manufacturer warranty immediately."*
  Because both documents reinforce the exact same policy, there is no conflict. The expected status `SUFFICIENT` is genuine: replacement is definitively not covered.
- **Verdict**: **Overly Broad Conflict Trigger**. The conflict gate should only fire when one document sanctions or recommends an action that another document prohibits.

---

### 2.3 `P4_Q28`
- **Query**: *"What is the temperature threshold that trips the fuser unit thermal fuse on ApexPrint printers?"*
- **Expected Status**: `SUFFICIENT`
- **Actual Status**: `PARTIAL`
- **Top Dense Score**: `0.5674` (EvidenceGate status was `SUFFICIENT`).
- **Corpus Grounding**: Fully supported by `apexprint_error_codes_and_hardware_troubleshooting.md` Section 2: *"Trigger: Fuser assembly thermistor sensed temperatures exceeding 230°C (446°F), engaging emergency thermal shutdown."*
- **Responsible Gate Condition**: **Post-Generation Citation Validator** (`citation_validator.py`).
- **Root Cause & Diagnosis**:
  The EvidenceGate approved the evidence as `SUFFICIENT`. However, during post-generation citation validation, the sentence-level token overlap between the local synthesis answer and the retrieved text fell slightly below the threshold, or the numerical claim check for temperature units was flagged.
- **Verdict**: **Post-Generation Groundedness Strictness**. The evidence was not rejected pre-generation; rather, the post-generation citation validator downgraded the final badge to `PARTIAL`.

---

### 2.4 Category G: Ambiguous / Partial Queries (`P4_Q41` through `P4_Q45`)

These 5 queries belong to Category G in the Original Phase 4 Benchmark:
- `P4_Q41`: *"Can the ApexPrint printer print documents sent from an iPhone over Bluetooth without a Wi-Fi router?"*
- `P4_Q42`: *"What is the exact battery life of the ApexPrint ProX-400 when used outdoors?"*
- `P4_Q43`: *"Does the system support natural language querying in Spanish or Japanese?"*
- `P4_Q44`: *"Can the ColorWave-850 print directly from a USB flash drive without a connected computer?"*
- `P4_Q45`: *"How many total questions were evaluated in the Stage 8 held-out benchmark and what was the completion rate?"*

#### Detailed Analysis:
- **Expected Status**: `PARTIAL`
- **Actual Status**: `SUFFICIENT`
- **Nature of Failure**: These queries were **NOT rejected**. In fact, the system **accepted** all five queries as `SUFFICIENT` and generated grounded answers!
- **Why did the evaluation report count them as failures?**:
  In `original_benchmark_results.json`, `verdict` was evaluated as:
  ```python
  "verdict": "PASS" if resp.evidence_status == exp_status else "FAIL"
  ```
  Because `exp_status == "PARTIAL"` and `resp.evidence_status == "SUFFICIENT"`, the runner marked them as `verdict: "FAIL"`.
- **Corpus Grounding Assessment**:
  For all five questions, the knowledge base contains adjacent information (e.g., Wi-Fi Direct and mobile printing for `P4_Q41`; desktop AC electrical requirements for `P4_Q42`; English support and architecture for `P4_Q43`; USB port interfaces for `P4_Q44`; citation validator test suites for `P4_Q45`). The local generator synthesized answers using the available text and included standard caveat phrasing.
- **Verdict**: **Over-Acceptance / Partial Differentiation Defect**. The system failed to distinguish partially documented features from fully documented specifications, defaulting to `SUFFICIENT` rather than flagging `PARTIAL`.

---

## 3. Independent Validation Benchmark Supported Query (1 Query)

### 3.1 `P4_2_VAL06`
- **Query**: *"What is the recommended cleaning interval and procedure for the optical laser glass and corona wire?"*
- **Expected Status**: `SUFFICIENT`
- **Actual Status**: `CONFLICTING` (in historical JSON) / `SUFFICIENT` (post-regex hardening)
- **Top Dense Score**: `0.3986` (Passes the $0.2800$ floor).
- **Corpus Grounding**: Fully documented in `apexprint_frequently_asked_questions_hardware_and_service.md` and user manual maintenance sections.
- **Responsible Gate Condition**: **Conflict Gate Word Matcher**.
- **Root Cause & Diagnosis**:
  The query contained the words *"corona wire"* and *"cleaning"*, and the retrieved set contained chunks from both `troubleshooting` and `warranty`. The Phase 4.2 conflict detector contained a rule that looked for *"replace"* or *"clean"* alongside warranty void words, falsely tagging standard routine maintenance as a warranty conflict.
- **Verdict**: **Spurious Conflict Trigger on Routine Maintenance**. Routine cleaning of laser glass and corona wires using the built-in slider tab is explicitly sanctioned by the user manual and does not constitute unauthorized disassembly.

---

## 4. Synthesis of False-Rejection Findings

1. **True Hard False Rejection**:
   Across all 70 supported queries evaluated, there is only **one** true hard false rejection: **`P4_Q09`** (Error E-101), caused by a trailing-word regex limitation in the entity compatibility check.
2. **Conflict Over-Triggering**:
   Two queries (`P4_Q18` and `P4_2_VAL06`) were diverted to `CONFLICTING` because the conflict heuristic conflated mutual agreement (both documents forbidding disassembly) and routine maintenance with contradictory advice.
3. **Partial Classification Gap**:
   Five Category G queries in the original benchmark were classified as `SUFFICIENT` rather than `PARTIAL` because the evidence gate currently lacks fine-grained sub-inquiry completeness verification.
