# Stage 8 Phase 4.3: Independent Validation Dataset & Label Integrity Audit

**Target Dataset Audited**: `evaluations/stage8_phase4_2/independent_validation_dataset.json` (32 Queries)  
**Corpus Knowledge Base**: `data/knowledge_base/` (43 indexed chunks across 8 document sources)  
**Date**: November 15, 2026  
**Auditor**: Evaluation Integrity & Independent Verification Engine  

---

## 1. Executive Summary

This audit independently reviews the 32-query dataset introduced in Stage 8 Phase 4.2 (`independent_validation_dataset.json`). The audit examines query authorship, distinctness from the original 50-query benchmark, taxonomy coverage across the 12 unsupported queries, and the factual justification of expected evidence status labels against the actual indexed Markdown corpus.

**Key Findings**:
1. **Authorship**: All 32 queries were authored internally during Stage 8 Phase 4.2 to stress-test the EvidenceGate. They were not reviewed by an independent third-party domain expert prior to execution.
2. **Distinctness**: The queries are genuinely distinct from the original Phase 4 benchmark, expanding into previously unqueried architectural components of the Project Dossier (vector distance metrics, RRF constants, chunking overlap, ingestion formats) and unseen external competitor brands (Ricoh, Lexmark, Kyocera).
3. **Diversity of Unsupported Queries**: The 12 unsupported queries successfully represent 7 distinct failure archetypes: competitor brand mismatches (3), unmentioned policy perils (2), misleading lexical overlap (1), pure alien out-of-domain (1), in-domain missing information (2), contradictory evidence (2), and partial multi-part evidence (1).
4. **Label Defects Discovered**: Two queries (`P4_2_VAL21` and `P4_2_VAL22`) had expected labels (`CONFLICTING`) that were **factually unjustified by the corpus**. In the actual indexed documents, no contradiction exists: both troubleshooting manuals and warranty agreements strictly prohibit unauthorized disassembly and electrical bypassing.

---

## 2. Query Distinctness Analysis

A lexical and semantic comparison between the 50 queries of the Original Phase 4 Benchmark and the 32 queries of the Independent Validation Dataset confirms that the new dataset introduces authentic novel evaluation targets:

| Evaluation Dimension | Original Phase 4 Benchmark (50 Qs) | Independent Validation Dataset (32 Qs) | Distinctness Assessment |
| :--- | :--- | :--- | :--- |
| **Competitor Hardware** | HP LaserJet M608, Canon PIXMA | Ricoh Aficio MP C4503, Lexmark CS720, Kyocera ECOSYS P3155dn | **100% Novel**: Evaluates unseen brands and alphanumeric product codes. |
| **Project Architecture** | General RAG/MCP overview, Stage 7B latency | Chunking overlap (50 chars), ChromaDB cosine metric, RRF $k=60$, upload file formats | **100% Novel**: Targets specific implementation constants from Project Dossier. |
| **Hardware Maintenance** | High-level printhead error E-101 | Corona wire cleaning slider tab, optical laser glass microfiber wiping procedure | **100% Novel**: Evaluates maintenance procedures documented in FAQ. |
| **Policy Exclusions** | Non-OEM consumables, general tampering | Operating outside electrical voltage limits (110V vs 220V), consumable yield depletion | **100% Novel**: Targets specific clauses in extended warranty documents. |
| **Unmentioned Perils** | Extraterrestrial meteor, nuclear radiation | Volcanic eruption ash, toxic chemical spills, spilled coffee/tea liquid damage | **100% Novel**: Stresses contractual silence without static peril list dependence. |

---

## 3. Comprehensive Audit of Expected Status Labels

Every query in the 32-query dataset was checked against the verbatim text of the indexed documents in `data/knowledge_base/`:

### 3.1 Supported Queries (`P4_2_VAL01` to `P4_2_VAL20` — 20 Queries)
- **`VAL01`–`VAL04`**: Fully supported by ProX-400 user manual and Project Dossier Section 3. Label `SUFFICIENT` is **JUSTIFIED**.
- **`VAL05`–`VAL07`**: Fully supported by troubleshooting guides and Dossier Section 3.4. Label `SUFFICIENT` is **JUSTIFIED**.
- **`VAL08`–`VAL11`**: Cross-document specifications, upload category routing, RRF formula, and MCP architecture are fully documented. Label `SUFFICIENT` is **JUSTIFIED**.
- **`VAL12`–`VAL13`**: Operating outside electrical limits and consumable exclusions are explicitly documented in warranty documents. Label `SUFFICIENT` is **JUSTIFIED**.
- **`VAL14`–`VAL16`**: Stage 7B benchmark metrics, 1,024 MB storage constraint, and 5 automated health check subsystems are documented in the Dossier. Label `SUFFICIENT` is **JUSTIFIED**.
- **`VAL17`–`VAL20`**: Subnet printing, supported file formats, EcoTank L3150 specs, and Wi-Fi reset are documented in manuals. Label `SUFFICIENT` is **JUSTIFIED**.

---

### 3.2 Unsupported Queries (`P4_2_VAL21` to `P4_2_VAL32` — 12 Queries)

#### `P4_2_VAL21`
- **Query**: *"Can I disassemble and replace the fuser unit myself using hand tools if Error E-204 persists?"*
- **Expected Label**: `CONFLICTING`
- **Corpus Verification**:
  - `apexprint_error_codes_and_hardware_troubleshooting.md` chunk `c0001`:
    > *"Warning: Do NOT attempt to disassemble the fuser assembly using a screwdriver or tools. Opening internal high-voltage or thermal assemblies voids warranty and risks severe electrical shock or burn injury."*
  - `apexprint_extended_warranty_and_exclusions.md` chunk `c0002`:
    > *"Unauthorized disassembly or opening the chassis voids the manufacturer warranty immediately."*
- **Label Audit Verdict**: **FLAWED EXPECTED LABEL**.
  The author assigned `CONFLICTING` assuming the troubleshooting guide explained component access while warranty voided it. However, the troubleshooting manual explicitly forbids hand-tool disassembly and confirms that doing so voids warranty. There is no contradiction. The query is answerable with definitive, non-conflicting negative advice. The correct status is `SUFFICIENT` (or `INSUFFICIENT` if answering whether disassembly is permitted under warranty).

#### `P4_2_VAL22`
- **Query**: *"Should I bypass the internal power supply if voltage fluctuations occur in the printing environment?"*
- **Expected Label**: `CONFLICTING`
- **Corpus Verification**:
  - `apexprint_prox400_user_manual.md` chunk `c0003` specifies voltage requirements and warns that unauthorized electrical modification voids warranty.
  - No document in the knowledge base recommends bypassing the power supply.
- **Label Audit Verdict**: **FLAWED EXPECTED LABEL**.
  Bypassing the power supply is not an action described with contradictory advice; it is an ungrounded, hazardous action absent from the knowledge base. The correct status is `INSUFFICIENT`, not `CONFLICTING`.

#### `P4_2_VAL23`
- **Query**: *"What is the standard warranty period and what is the exact physical mailing address for sending international return merchandise?"*
- **Expected Label**: `PARTIAL`
- **Corpus Verification**:
  - Standard warranty period (12 months) is in `apexprint_standard_limited_warranty_policy.md`.
  - An international physical mailing street address is nowhere in the corpus.
- **Label Audit Verdict**: **JUSTIFIED LABEL**.
  This is a textbook multi-part question with partial coverage.

#### `P4_2_VAL24`–`P4_2_VAL26` (Competitor Mismatches: Ricoh, Lexmark, Kyocera)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: None of these brands or model numbers exist in the corpus.
- **Label Audit Verdict**: **JUSTIFIED LABELS**.

#### `P4_2_VAL27`–`P4_2_VAL28` (Unmentioned Policy Perils: Volcanic ash, Coffee/tea spills)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: Neither volcanic eruption ash nor coffee/tea beverage spills are mentioned in warranty coverage or exclusions. Contractual silence applies.
- **Label Audit Verdict**: **JUSTIFIED LABELS**.

#### `P4_2_VAL29` (Misleading Lexical Overlap: United Airlines carry-on dimensions)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: United Airlines baggage limits do not exist in the corpus.
- **Label Audit Verdict**: **JUSTIFIED LABEL**.

#### `P4_2_VAL30` (Pure Alien OOD: Europa orbital velocity)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: Celestial orbital mechanics do not exist in the corpus.
- **Label Audit Verdict**: **JUSTIFIED LABEL**.

#### `P4_2_VAL31` (In-Domain Missing Info: Wholesale bulk dealer discount percentage)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: The ColorWave-850 is indexed, but dealer wholesale discounts are absent from all manuals.
- **Label Audit Verdict**: **JUSTIFIED LABEL**.

#### `P4_2_VAL32` (In-Domain Missing Info: AWS EC2 hosting cost)
- **Expected Label**: `INSUFFICIENT`
- **Corpus Verification**: Cloud hosting costs on AWS EC2/Kubernetes are absent from the Project Dossier.
- **Label Audit Verdict**: **JUSTIFIED LABEL**.

---

## 4. Proposed Label Corrections (Preserved Separately)

In accordance with strict audit protocol, historical raw benchmark files are never silently altered. The following table records proposed corrections for benchmark evolution:

| Query ID | Query Text | Historical Expected Label | Audited True Expected Label | Evidence & Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **`P4_2_VAL21`** | Can I disassemble and replace the fuser unit myself using hand tools if Error E-204 persists? | `CONFLICTING` | **`SUFFICIENT`** | Both troubleshooting manual and warranty policy agree that hand-tool fuser disassembly is hazardous and voids warranty. Answer is definitively supported. |
| **`P4_2_VAL22`** | Should I bypass the internal power supply if voltage fluctuations occur in the printing environment? | `CONFLICTING` | **`INSUFFICIENT`** | Bypassing internal power supply is an undocumented, unsanctioned action absent from the corpus. There is no document conflict. |
| **`P4_2_VAL23`** | What is the standard warranty period and what is the exact physical mailing address for sending international return merchandise? | `PARTIAL` | **`PARTIAL`** | Retained as genuine: warranty period is documented; international mailing address is absent. |
| **`P4_2_VAL31`** | What is the wholesale bulk dealer discount percentage for purchasing 500 units of the ColorWave-850? | `INSUFFICIENT` | **`INSUFFICIENT`** | Retained as genuine: product exists, but commercial pricing/discounts are absent. |
