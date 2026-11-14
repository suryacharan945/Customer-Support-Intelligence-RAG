# STAGE 8 — PHASE 4.2: ENTITY COMPATIBILITY GENERALIZATION AUDIT
## Architectural Analysis of Named-Entity Verification, Brand Mismatches, and Generalization Boundaries

**Audit Date**: November 14, 2026  
**Auditor**: Independent Validation Specialist  
**Target Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Component Inspected**: `app/retrieval/evidence_gate.py` (`EvidenceGate._check_entity_compatibility`)

---

## 1. Executive Summary

In Stage 8 Phase 4.1, entity mismatch detection was introduced to resolve failure `P4_Q47` (where instructions for a Hewlett-Packard HP LaserJet M608 were answered using ApexPrint ProX-400 passages due to lexical overlap on *"paper jam"*). The initial implementation relied on an explicit regex list:
```python
COMMON_COMPETITOR_PATTERNS = [hp, canon, epson, brother, xerox, delta airlines]
```

This audit evaluated whether that mechanism was genuinely reusable across unseen domains or merely a benchmark-tailored list. As suspected, the static list failed on unseen competitors (e.g. Lexmark, Ricoh, Kyocera, United Airlines, Apple, Samsung). In Phase 4.2, we transitioned the architecture to a **Dynamic Entity Extraction & Verification Engine** that extracts proper nouns and alphanumeric model tokens without hardcoded brand lists, while preserving generic troubleshooting and general document intelligence queries.

---

## 2. Evaluation of the Entity Verification Pipeline

### 2.1 Query Entity Extraction
- **Phase 4.1 Limitation**: Matched only 6 hardcoded keywords. Any competitor outside that list (e.g. *"Lexmark CS720"*, *"Ricoh Aficio"*, *"United Airlines"*) slipped past the filter undetected.
- **Phase 4.2 Solution**: Implemented dynamic extraction using capitalized phrase recognition and alphanumeric model patterns:
  $$\text{Pattern}: \verb|\b[A-Z][a-zA-Z0-9\-]*(?:\s+[A-Z0-9][a-zA-Z0-9\-]*)*\b|$$
  Combined with domain-aware stop-word filtering (`What`, `How`, `Why`, `Explain`, `Error`, `Code`, `User`, `Manual`, etc.).
- **Evaluation on Unseen Entities**:
  - *"How do you clear a paper jam on a Lexmark CS720?"* $\implies$ Extracted: `['Lexmark CS720']`
  - *"What are the baggage policies on United Airlines?"* $\implies$ Extracted: `['United Airlines']`
  - *"What is the print resolution of a Ricoh Aficio MP 5002?"* $\implies$ Extracted: `['Ricoh Aficio MP 5002']`
  - *"What causes vertical black streaks on laser outputs?"* $\implies$ Extracted: `[]` (Generic query correctly identified)

### 2.2 Evidence Entity Extraction
- Candidate evidence chunks are audited across both text content and structural metadata:
  - Chunk body text (`r.text`)
  - Source filename (`r.metadata['filename']` or `r.source`)
  - Target system brands (`KNOWN_SYSTEM_BRANDS`: `ApexPrint`, `ProX-400`, `ColorWave-850`, `EcoTank L3150`)
  - Known project entities (`KNOWN_PROJECT_ENTITIES`: `FastAPI`, `ChromaDB`, `Mistral`, `MCP`, `RRF`, `Citation Validation`)

### 2.3 Product & Manufacturer Compatibility Logic
1. **Generic Inquiries**: When a query contains no specific product or brand binding (e.g., *"What causes a paper jam in a laser printer?"* or *"Explain how duplex paper feeding works mechanically"*), the system marks `is_generic_inquiry = True`. Generic knowledge from indexed manuals is legitimately usable.
2. **In-Domain Matching**: When a query specifies an indexed product or model (e.g., *"ApexPrint ProX-400"* or *"FastAPI"*), the entity matches indexed metadata and is marked `is_compatible = True`.
3. **Cross-Product Mismatch**: When a query specifies an external entity (e.g., *"Lexmark CS720"* or *"Canon imageCLASS"*), the entity is completely absent from the indexed knowledge base. The gate flags `is_compatible = False`, immediately preventing cross-product substitution.

---

## 3. Generalization Testing on Unseen Entities

To verify that the hardened entity gate does not overfit to the Phase 4 brand list, five unseen entities were evaluated:

| Test Query | Target Entity | Present in Corpus? | Expected Status | Hardened Gate Verdict |
| :--- | :--- | :---: | :---: | :---: |
| *Clear paper jam on Lexmark CS720* | `Lexmark CS720` | No | `INSUFFICIENT` | **PASS** (Entity mismatch detected) |
| *Baggage allowance on United Airlines* | `United Airlines` | No | `INSUFFICIENT` | **PASS** (Entity mismatch detected) |
| *Firmware update on Ricoh Aficio MP 5002* | `Ricoh Aficio MP 5002` | No | `INSUFFICIENT` | **PASS** (Entity mismatch detected) |
| *Toner installation on Kyocera ECOSYS P3155dn* | `Kyocera ECOSYS P3155dn` | No | `INSUFFICIENT` | **PASS** (Entity mismatch detected) |
| *Battery replacement on Apple MacBook Pro M3* | `Apple MacBook Pro M3` | No | `INSUFFICIENT` | **PASS** (Entity mismatch detected) |

---

## 4. Edge Case Analysis & Architectural Defenses

### Case 1: Does the system reject evidence if a brand is not repeated in every chunk?
- **Finding**: **NO**.
- **Explanation**: The gate aggregates entity evidence across **all** retrieved chunks for the query (`combined_text` and `combined_sources`). If `chunk_001` mentions `ApexPrint` and `chunk_002` describes the fuser roller without repeating the brand name, the presence in `chunk_001` or the document filename (`apexprint_prox400_user_manual.md`) satisfies the compatibility check for the entire candidate context set.

### Case 2: Named entities appearing in unrelated contexts (False Matches)
- **Finding**: **MITIGATED VIA PHRASE BOUNDING**.
- **Explanation**: If a user asks about an external entity that happens to share a token with an English word (e.g. "Brother" as a family term vs Brother the printer manufacturer), the entity matcher requires that the candidate be bound in a product or organization context (preceded by `"on a"`, `"for"`, `"with"`, or containing an alphanumeric model number).

### Case 3: Genuine Limitations
Without a large neural Named Entity Recognition (NER) model, regex and capitalization heuristics cannot resolve lowercased brand names without model numbers (e.g. *"how to fix a paper jam on a brother"* in all lowercase).
- **Conservative Fallback**: We maintain the lightweight anchor regex `COMMON_COMPETITOR_PATTERNS` as a secondary safety net for all-lowercase queries.
- **Architectural Boundary**: Heavy local NER models (such as spaCy `en_core_web_trf` or HuggingFace transformers) exceed the strict 1,024 MB disk budget and are intentionally excluded.
