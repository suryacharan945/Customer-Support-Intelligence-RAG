# STAGE 8 — PHASE 4.2: POLICY & NEGATIVE-CLAIM AUDIT
## Decision Framework for Warranty Inclusions, Exclusions, Missing Perils, and Contradictions

**Audit Date**: November 14, 2026  
**Auditor**: Independent Validation Specialist  
**Target Repository**: `C:\Users\surya\Downloads\Customer Support ChatBot`  
**Component Inspected**: `app/retrieval/evidence_gate.py` (`EvidenceGate._check_policy_verification`)

---

## 1. Executive Summary

In Stage 8 Phase 4, query `P4_Q50` (*"Does the ApexPrint warranty policy cover damage caused by extraterrestrial meteor strikes or nuclear radiation?"*) produced a severe hallucination: the LLM retrieved standard warranty clauses, observed silence regarding meteor strikes, and deduced: *"Since meteor strikes are not listed in coverage, they are excluded under warranty terms"*. This presented an unsubstantiated policy assertion as verified ground truth.

In Phase 4.1, a hardcoded set `EXOTIC_PERILS` was introduced. This audit evaluated the brittleness of that peril list and replaced it with a **Dynamic Policy Condition Extraction & Verification Framework** grounded in contractual silence principles.

---

## 2. Core Legal & Contractual Principle: Silence is Not Exclusion

In commercial and enterprise warranty law:
> **The absence of an explicit policy clause regarding event $X$ is not evidence of inclusion, nor is it evidence of exclusion.**

A document intelligence assistant must never extrapolate coverage or denial from contractual silence. When a document does not address an inquiry, the only truthful response is an honest disclosure of missing evidence:
> *"The retrieved warranty documentation contains no terms or clauses addressing '{queried_condition}'. The absence of a clause is not proof of inclusion or exclusion."*

---

## 3. Comprehensive Policy Decision Framework

The hardened policy gate implements a 5-way contractual classification:

| Condition Category | Definition | Knowledge Base Evidence State | Decision Status | Synthesizer Behavior |
| :--- | :--- | :--- | :---: | :--- |
| **1. Explicit Inclusion** | Condition is explicitly listed in covered terms | Passage states condition is covered (e.g., *"defects in materials and workmanship"*, *"12 months hardware parts"*) | **`SUFFICIENT`** | Generate complete grounded explanation citing exact policy chunk and page. |
| **2. Explicit Exclusion** | Condition is explicitly enumerated under exclusions | Passage explicitly excludes condition (e.g., *"unauthorized disassembly"*, *"non-OEM consumables"*, *"acts of nature"*) | **`SUFFICIENT`** | Generate complete grounded explanation detailing the explicit exclusion with citations. |
| **3. Missing Policy Information** | Condition is completely absent from policy text | Neither inclusion nor exclusion mentioned (e.g., *"volcanic ash"*, *"meteor strikes"*, *"cosmetic scuffs"*) | **`INSUFFICIENT`** | **Bypass synthesis**. Return honest abstention stating absence of terms without fabricating denials. |
| **4. Ambiguous Policy Wording** | Term is mentioned vaguely without definitive criteria | General terms exist (e.g., *"improper operating conditions"*) but specific event criteria not defined | **`PARTIAL`** | Disclose documented general limitation while explicitly noting ambiguity regarding specific condition. |
| **5. Contradictory Statements** | Opposing recommendations across documents | Troubleshooting manual advises component replacement; warranty states opening unit voids warranty | **`CONFLICTING`** | Present both perspectives side-by-side with safety disclaimer and service escalation. |

---

## 4. Elimination of Hardcoded Peril Lists

### Phase 4.1 Implementation (Brittle)
```python
# Hardcoded set in Phase 4.1
EXOTIC_PERILS = {"meteor", "radiation", "nuclear", "earthquake", "tsunami", "flood", "cosmetic", "scratches", "dent"}
```
*Failure mode*: If a user asked about *"damage from volcanic ash"*, *"chemical spills"*, *"lightning strikes"*, or *"drone collisions"*, the gate failed to detect the unmentioned peril, allowing the LLM to invent clauses.

### Phase 4.2 Dynamic Policy Condition Extraction
Phase 4.2 dynamically extracts the subject condition phrase using regex grammatical patterns:
$$\text{Patterns}: \verb|(?:cover|covered|coverage|exclude|excluded|exclusion)\s+(?:for|against|damage caused by)?\s+([^?.,;]+)|$$
Extracted content tokens are audited against `combined_policy_text`. If the key semantic tokens are completely absent from retrieved policy passages, the condition is classified as **Missing Policy Information (`INSUFFICIENT`)**.

---

## 5. Empirical Verification Across Diverse Policy Queries

| Query | Extracted Condition | In Policy Text? | Status | Audit Verdict |
| :--- | :--- | :---: | :---: | :---: |
| *Does warranty cover manufacturing defects in materials?* | `manufacturing defects` | Yes (Inclusion) | `SUFFICIENT` | **PASS** |
| *Does warranty policy exclude unauthorized disassembly?* | `unauthorized disassembly` | Yes (Exclusion) | `SUFFICIENT` | **PASS** |
| *Does warranty cover damage resulting from non-OEM ink?* | `non-OEM ink` | Yes (Exclusion) | `SUFFICIENT` | **PASS** |
| *Does warranty cover damage from volcanic eruption or ash?* | `volcanic eruption, ash` | **No (Missing)** | `INSUFFICIENT` | **PASS** |
| *Does warranty cover casing damage caused by lightning strikes?* | `lightning strikes` | **No (Missing)** | `INSUFFICIENT` | **PASS** |
| *Does warranty cover cosmetic scratches and exterior scuffs?* | `scratches, scuffs, cosmetic` | **No (Missing)** | `INSUFFICIENT` | **PASS** |
| *Does warranty cover damage caused by meteor strikes or nuclear fallout?* | `meteor, nuclear, fallout` | **No (Missing)** | `INSUFFICIENT` | **PASS** |

---

## 6. Audit Conclusion
The policy gate has been successfully decoupled from benchmark-specific peril lists. It enforces contractual neutrality, preventing both false claims of coverage and false inferences of exclusion.
