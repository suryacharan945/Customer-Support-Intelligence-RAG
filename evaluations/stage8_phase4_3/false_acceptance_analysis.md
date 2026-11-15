# Stage 8 Phase 4.3: In-Depth Investigation of False Acceptances

**Benchmark Audited**: Stage 8 Phase 4.2 Independent Validation Dataset (32 Queries)  
**Historical Result File**: `evaluations/stage8_phase4_2/independent_validation_results.json`  
**Date**: November 15, 2026  
**Auditor**: Evaluation Integrity & Independent Verification Engine  

---

## 1. Overview

In Stage 8 Phase 4.2, the 32-question independent validation dataset yielded 4 queries labeled as unsupported (`is_supported: false`) that were classified by the system as answerable (`actual_status: "SUFFICIENT"`), representing a False Acceptance Rate (FAR) of **33.33%** (4 / 12 unsupported queries).

This audit conducts an exhaustive post-mortem of all four queries, tracing the execution pipeline from category classification, dense and sparse retrieval, reciprocal rank fusion, entity compatibility, policy verification, evidence gate evaluation, through to answer generation and citation validation.

---

## 2. Detailed Query Investigations

### 2.1 Query 1: `P4_2_VAL21`

- **Query ID**: `P4_2_VAL21`
- **Exact Query**: *"Can I disassemble and replace the fuser unit myself using hand tools if Error E-204 persists?"*
- **Expected Evidence Status**: `CONFLICTING`
- **Actual Evidence Status**: `SUFFICIENT`
- **Taxonomy Category**: Contradictory Evidence
- **Dataset Author Rationale**: *"Troubleshooting manual explains component access while warranty policy explicitly voids warranty for unauthorized disassembly."*

#### Retrieval Diagnostic Profile
- **Selected Retrieval Categories**: `['troubleshooting']` (single category selected by router due to strong hardware error intent).
- **Retrieval Mode**: `multi_context` (Hybrid ChromaDB dense + BM25Okapi sparse + RRF fusion).
- **Retrieved Documents & Chunks**:
  1. `apexprint_error_codes_and_hardware_troubleshooting.md` | Chunk: `doc_trou_54171a85acbc_c0001` (Category: `troubleshooting`)
     - Dense Similarity: **0.6734** | Sparse Score (BM25): **1.0000** | RRF Score: **1.000000**
  2. `apexprint_error_codes_and_hardware_troubleshooting.md` | Chunk: `doc_trou_54171a85acbc_c0002` (Category: `troubleshooting`)
     - Dense Similarity: **0.6314** | Sparse Score (BM25): **0.6891** | RRF Score: **0.983900**
  3. `apexprint_error_codes_and_hardware_troubleshooting.md` | Chunk: `doc_trou_54171a85acbc_c0000` (Category: `troubleshooting`)
     - Dense Similarity: **0.2867** | Sparse Score (BM25): **0.2468** | RRF Score: **0.968300**
  4. `apexprint_prox400_wifi_and_connectivity_troubleshooting.md` | Chunk: `doc_trou_ee280f83aa9f_c0002` (Category: `troubleshooting`)
     - Dense Similarity: **0.1440** | Sparse Score (BM25): **0.0423** | RRF Score: **0.947300**
  5. `apexprint_prox400_wifi_and_connectivity_troubleshooting.md` | Chunk: `doc_trou_ee280f83aa9f_c0000` (Category: `troubleshooting`)
     - Dense Similarity: **0.1378** | Sparse Score (BM25): **0.1128** | RRF Score: **0.944300**

#### Evidence Gate Decision
- **Similarity Floor Passed**: True (Top dense score: **0.6734** $\ge 0.2800$).
- **Entity Compatibility**: `is_compatible=True` (Query targets ApexPrint Error E-204).
- **Policy Verification**: `is_policy_query=False` (Query categorized as troubleshooting resolution).
- **Cross-Category Conflict Decision**: Evaluated as `False`. The conflict detector requires chunks from both `troubleshooting` AND `warranty` categories (`if "troubleshooting" in categories and "warranty" in categories:`). Because the query analyzer assigned category `['troubleshooting']` exclusively, zero warranty chunks were retrieved.
- **Final Gate Decision**: `SUFFICIENT`. Reason: *"Evidence meets calibrated similarity threshold and entity/domain compatibility criteria."*

#### Generation & Grounding Check
- **Generation Invoked**: Yes, `LOCAL_GROUNDED_SYNTHESIS` was executed.
- **Generated Answer Content**:
  > *"### 1. Executive Summary / Direct Answer\nError Code E-204: Fuser Unit Overheat Protection Trigger: Fuser assembly thermistor sensed temperatures exceeding 230°C (446°F), engaging emergency thermal shutdown...\nWarning: Do NOT attempt to disassemble the fuser assembly using a screwdriver or tools. Opening internal high-voltage or thermal assemblies voids warranty and risks severe electrical shock or burn injury. [Source: apexprint_error_codes_and_hardware_troubleshooting.md, Page: 1]"*
- **Did Final Answer Contain Unsupported Claims?**: **NO**. The answer was 100% grounded and verbatim supported by the troubleshooting manual.
- **Exact Root Cause & Label Review**:
  This is a **Dataset Labeling Defect**. The author who constructed the dataset assumed that the troubleshooting manual told the user how to disassemble the fuser while the warranty policy prohibited it, thereby creating a contradiction. In the actual indexed corpus, however, `apexprint_error_codes_and_hardware_troubleshooting.md` chunk `c0001` explicitly warns: *"Do NOT attempt to disassemble the fuser assembly using a screwdriver or tools. Opening internal high-voltage or thermal assemblies voids warranty..."*
  Both the troubleshooting guide and the warranty agreement are in complete harmony: unauthorized user disassembly is prohibited and voids warranty. The system retrieved the troubleshooting manual and accurately answered the question.

---

### 2.2 Query 2: `P4_2_VAL22`

- **Query ID**: `P4_2_VAL22`
- **Exact Query**: *"Should I bypass the internal power supply if voltage fluctuations occur in the printing environment?"*
- **Expected Evidence Status**: `CONFLICTING`
- **Actual Evidence Status**: `SUFFICIENT`
- **Taxonomy Category**: Contradictory Evidence
- **Dataset Author Rationale**: *"Troubleshooting recommends power conditioning while warranty policy warns tampering with power components terminates warranty."*

#### Retrieval Diagnostic Profile
- **Selected Retrieval Categories**: `[]` (Broad general document query).
- **Retrieval Mode**: `multi_context`.
- **Retrieved Documents & Chunks**:
  1. `apexprint_prox400_user_manual.md` | Chunk: `doc_prod_de7386b29af7_c0003` (Category: `product_manual`)
     - Dense Similarity: **0.3491** | Sparse Score (BM25): **1.0000** | RRF Score: **1.000000**
  2. `apexprint_error_codes_and_hardware_troubleshooting.md` | Chunk: `doc_trou_54171a85acbc_c0001` (Category: `troubleshooting`)
     - Dense Similarity: **0.3400** | Sparse Score (BM25): **0.5943** | RRF Score: **0.984000**
  3. `apexprint_extended_warranty_and_exclusions.md` | Chunk: `doc_warr_6bcedacd5b00_c0001` (Category: `warranty`)
     - Dense Similarity: **0.2898** | Sparse Score (BM25): **0.5644** | RRF Score: **0.947600**
  4. `apexprint_standard_limited_warranty_policy.md` | Chunk: `doc_warr_11757ad6d7b8_c0000` (Category: `warranty`)
     - Dense Similarity: **0.2797** | Sparse Score (BM25): **0.5704** | RRF Score: **0.944900**
  5. `apexprint_extended_warranty_and_exclusions.md` | Chunk: `doc_warr_6bcedacd5b00_c0002` (Category: `warranty`)
     - Dense Similarity: **0.4272** | Sparse Score (BM25): **0.2115** | RRF Score: **0.934400**

#### Evidence Gate Decision
- **Similarity Floor Passed**: True (Top dense score: **0.4272** $\ge 0.2800$).
- **Entity Compatibility**: `is_compatible=True` (General inquiry without competitor entity).
- **Policy Verification**: `is_policy_query=False` (Query did not match warranty coverage trigger).
- **Cross-Category Conflict Decision**: Evaluated as `False`. In `_check_conflicting_evidence`:
  The query did not contain conflict trigger keywords (`disassemble`, `disassembly`, `void`, `tamper`, `repair myself`, `conflict`, `contradict`). The word *"bypass"* was not present in the conflict lexicon.
- **Final Gate Decision**: `SUFFICIENT`. Reason: *"Evidence meets calibrated similarity threshold and entity/domain compatibility criteria."*

#### Generation & Grounding Check
- **Generation Invoked**: Yes, `LOCAL_GROUNDED_SYNTHESIS` was executed.
- **Generated Answer Content**:
  The system synthesized electrical specifications from `apexprint_prox400_user_manual.md` (voltage limits: 110V-127V / 220V-240V) and noted the warranty exclusion regarding step-down transformers and power supply destruction.
- **Did Final Answer Contain Unsupported Claims?**: The answer cited valid electrical specs, but did not directly address whether the user should "bypass" the power supply because "bypassing the power supply" is completely absent from the documentation.
- **Exact Root Cause & Label Review**:
  1. **Dataset Mislabeling**: There is no contradiction in the corpus. No document advises "bypassing" the power supply; the act is dangerous and prohibited. The expected label should have been `INSUFFICIENT` (or answered with explicit electrical exclusion), not `CONFLICTING`.
  2. **Lexical Attractor**: Dense similarity reached 0.4272 because words like "power supply", "voltage", and "environment" match electrical specification sections in the user manual. The gate lacked a predicate-level check to confirm that the queried action ("bypass") was documented.

---

### 2.3 Query 3: `P4_2_VAL23`

- **Query ID**: `P4_2_VAL23`
- **Exact Query**: *"What is the standard warranty period and what is the exact physical mailing address for sending international return merchandise?"*
- **Expected Evidence Status**: `PARTIAL`
- **Actual Evidence Status**: `SUFFICIENT`
- **Taxonomy Category**: Partial Evidence
- **Dataset Author Rationale**: *"Query contains two factual sub-questions; one is documented while the second is absent from the knowledge base."*

#### Retrieval Diagnostic Profile
- **Selected Retrieval Categories**: `[]` (Broad multi-category query).
- **Retrieval Mode**: `multi_context`.
- **Retrieved Documents & Chunks**:
  1. `apexprint_standard_limited_warranty_policy.md` | Chunk: `doc_warr_11757ad6d7b8_c0001` (Category: `warranty`)
     - Dense Similarity: **0.4769** | Sparse Score (BM25): **0.8521** | RRF Score: **1.000000**
  2. `apexprint_standard_limited_warranty_policy.md` | Chunk: `doc_warr_11757ad6d7b8_c0000` (Category: `warranty`)
     - Dense Similarity: **0.4249** | Sparse Score (BM25): **0.6893** | RRF Score: **0.977900**
  3. `apexprint_extended_warranty_and_exclusions.md` | Chunk: `doc_warr_6bcedacd5b00_c0002` (Category: `warranty`)
     - Dense Similarity: **0.2927** | Sparse Score (BM25): **0.7186** | RRF Score: **0.956500**
  4. `apexprint_extended_warranty_and_exclusions.md` | Chunk: `doc_warr_6bcedacd5b00_c0001` (Category: `warranty`)
     - Dense Similarity: **0.4215** | Sparse Score (BM25): **0.5410** | RRF Score: **0.945900**
  5. `apexprint_frequently_asked_questions_hardware_and_service.md` | Chunk: `doc_faq_e1d7f9f8c9ad_c0001` (Category: `faq`)
     - Dense Similarity: **0.1791** | Sparse Score (BM25): **1.0000** | RRF Score: **0.921400**

#### Evidence Gate Decision
- **Similarity Floor Passed**: True (Top dense score: **0.4769** $\ge 0.2800$).
- **Entity Compatibility**: `is_compatible=True`.
- **Policy Verification**: `is_policy_query=True`, `is_explicitly_documented=True` (Treated as informational warranty query because it begins with *"What is"*).
- **Final Gate Decision**: `SUFFICIENT`. Reason: *"Evidence meets calibrated similarity threshold and entity/domain compatibility criteria."*

#### Generation & Grounding Check
- **Generation Invoked**: Yes, `LOCAL_GROUNDED_SYNTHESIS` was executed.
- **Generated Answer Content**:
  The system answered the first sub-question (standard warranty period: 12 months) and detailed the 4-step RMA return procedure (obtain RMA number, package unit, prepaid shipping). However, it did not provide a physical international mailing address because no street address exists in the corpus.
- **Did Final Answer Contain Unsupported Claims?**: No hallucinated address was produced. The answer omitted the address and described the support ticket process.
- **Exact Root Cause**:
  **Absence of Multi-Part Conjunction Coverage**: The query is compound:
  - Sub-inquiry 1: *"What is the standard warranty period"* (Documented: 12 months).
  - Sub-inquiry 2: *"what is the exact physical mailing address for sending international return merchandise"* (Undocumented).
  Because Sub-inquiry 1 achieved high dense and sparse similarity ($0.4769$), the overall retrieval score easily cleared the $0.2800$ floor. The EvidenceGate lacked a multi-part coverage analyzer to evaluate whether each independent conjunction in an *"and"* compound query has topical support in the retrieved passages.

---

### 2.4 Query 4: `P4_2_VAL31`

- **Query ID**: `P4_2_VAL31`
- **Exact Query**: *"What is the wholesale bulk dealer discount percentage for purchasing 500 units of the ColorWave-850?"*
- **Expected Evidence Status**: `INSUFFICIENT`
- **Actual Evidence Status**: `SUFFICIENT`
- **Taxonomy Category**: In-Domain Missing Information
- **Dataset Author Rationale**: *"Valid in-domain hardware product (ColorWave-850), but commercial dealer wholesale discounts are not in knowledge base."*

#### Retrieval Diagnostic Profile
- **Selected Retrieval Categories**: `['product_manual']`.
- **Retrieval Mode**: `multi_context`.
- **Retrieved Documents & Chunks**:
  1. `apexprint_colorwave850_user_manual.md` | Chunk: `doc_prod_a92c5cafaf32_c0000` (Category: `product_manual`)
     - Dense Similarity: **0.3644** | Sparse Score (BM25): **0.7744** | RRF Score: **1.000000**
  2. `apexprint_prox400_user_manual.md` | Chunk: `doc_prod_de7386b29af7_c0001` (Category: `product_manual`)
     - Dense Similarity: **0.2771** | Sparse Score (BM25): **0.5519** | RRF Score: **0.983900**
  3. `apexprint_ecotank_l3150_specs.txt` | Chunk: `doc_prod_c4f75309780c_c0000` (Category: `product_manual`)
     - Dense Similarity: **0.2648** | Sparse Score (BM25): **0.5019** | RRF Score: **0.962200**
  4. `apexprint_prox400_user_manual.md` | Chunk: `doc_prod_de7386b29af7_c0002` (Category: `product_manual`)
     - Dense Similarity: **0.2574** | Sparse Score (BM25): **0.2201** | RRF Score: **0.906100**
  5. `AI Customer Support Intelligence Platform - Project Dossier.pdf` | Chunk: `doc_prod_4d6578a53efe_p4_c0002` (Category: `product_manual`)
     - Dense Similarity: **0.1659** | Sparse Score (BM25): **0.2983** | RRF Score: **0.889300**

#### Evidence Gate Decision
- **Similarity Floor Passed**: True (Top dense score: **0.3644** $\ge 0.2800$).
- **Entity Compatibility**: `is_compatible=True` (Query names *"ColorWave-850"*, an authentic in-domain ApexPrint product).
- **Policy Verification**: `is_policy_query=False` (Not a warranty policy query).
- **Final Gate Decision**: `SUFFICIENT`. Reason: *"Evidence meets calibrated similarity threshold and entity/domain compatibility criteria."*

#### Generation & Grounding Check
- **Generation Invoked**: Yes, `LOCAL_GROUNDED_SYNTHESIS` was executed.
- **Generated Answer Content**:
  The system synthesized an answer explaining the ColorWave-850 print speed (35 ppm color / 40 ppm mono), EcoTank specs, and ProX-400 tray capacities. It completely ignored the question about wholesale discounts.
- **Did Final Answer Contain Unsupported Claims?**: The generated text was grounded in the user manual chunks, but it was **completely non-responsive / topic-divergent** regarding wholesale discounts.
- **Exact Root Cause**:
  **In-Domain Subject Attractor with Missing Predicate**:
  This is the most critical failure mode in entity-aware RAG pipelines. When an inquiry queries a legitimate in-domain entity (`ColorWave-850`), the dense embeddings for the entity match the document strongly ($0.3644 \ge 0.2800$), and BM25 matches lexical tokens like *"500"* (Tray 2 has 500-sheet capacity) and *"purchasing"*.
  However, the core information target—the predicate words **`discount`**, **`wholesale`**, **`dealer`**—have **zero presence** anywhere in the entire knowledge base.
  Because the similarity floor checks the overall semantic vector and not predicate term containment, the query leaked through the evidence gate.

---

## 3. Summary of Failure Mechanisms

| Query ID | Expected Status | Actual Status | Failure Classification | Architectural Mechanism | Required Solution |
| :--- | :---: | :---: | :---: | :--- | :--- |
| **`P4_2_VAL21`** | CONFLICTING | SUFFICIENT | **Dataset Label Defect** | The corpus does not conflict; both manual and warranty prohibit disassembly. | Correct dataset expected label to `SUFFICIENT`. |
| **`P4_2_VAL22`** | CONFLICTING | SUFFICIENT | **Dataset Label Defect & Subject Attractor** | "Bypassing" power supply is not in conflict; it is an undocumented dangerous action. | Correct dataset expected label to `INSUFFICIENT`; add predicate check. |
| **`P4_2_VAL23`** | PARTIAL | SUFFICIENT | **Compound Conjunction Leak** | Sub-query 1 (period) is documented; Sub-query 2 (address) is undocumented. High score on sub-query 1 passed the gate. | Implement Multi-Part Conjunction Coverage Check in EvidenceGate. |
| **`P4_2_VAL31`** | INSUFFICIENT | SUFFICIENT | **In-Domain Entity Attractor** | Query names valid product (`ColorWave-850`), but core predicates (`wholesale`, `discount`) have zero corpus presence. | Implement Query-Evidence Predicate Containment Check in EvidenceGate. |
