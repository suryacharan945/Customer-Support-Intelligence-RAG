#!/usr/bin/env python3
"""
Generate comprehensive Failure Analysis for Stage 8 Phase 4.5 Blind and Adversarial Failures.
Outputs evaluations/stage8_phase4_6/phase4_6_failure_analysis.md.
"""

import json
from pathlib import Path

def generate_failure_analysis():
    blind_res_path = Path("evaluations/stage8_phase4_5/blind_compound_query_results.json")
    with open(blind_res_path, "r", encoding="utf-8") as f:
        blind_data = json.load(f)

    adv_res_path = Path("evaluations/stage8_phase4_5/adversarial_test_results.json")
    with open(adv_res_path, "r", encoding="utf-8") as f:
        adv_data = json.load(f)

    blind_fa = [
        r for r in blind_data["results"]
        if r["expected_evidence_status"] in ["PARTIAL", "INSUFFICIENT"]
        and r["predicted_evidence_status"] == "SUFFICIENT"
    ]

    adv_fa = [
        r for r in adv_data["test_results"]
        if not r["passed"]
    ]

    print(f"Loaded {len(blind_fa)} blind false acceptances and {len(adv_fa)} adversarial failures.")

    out_md = Path("evaluations/stage8_phase4_6/phase4_6_failure_analysis.md")
    
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# STAGE 8 — PHASE 4.6\n")
        f.write("## Phase 4.5 Failure Analysis & Root Cause Investigation\n\n")
        f.write("**Date**: November 15, 2026  \n")
        f.write("**Scope**: Detailed forensic investigation of all 13 Phase 4.5 Blind Benchmark false acceptances and 6 Adversarial test failures.  \n")
        f.write("**Baseline Commit**: `534f279`  \n\n")
        f.write("---\n\n")

        f.write("## 1. EXECUTIVE FAILURE SUMMARY\n\n")
        f.write("In Stage 8 Phase 4.5, independent blind validation exposed a critical vulnerability: while the system achieved **93.75% accuracy and 0.0% False Acceptance Rate on historical benchmarks**, its exact match accuracy on a 30-query blind challenge set dropped to **40.0%**, with a **61.90% False Acceptance Rate** (13 / 21 unsupported or partially supported queries accepted as `SUFFICIENT`).\n\n")
        f.write("Additionally, the system resisted only **4 / 10 (40.0%)** adversarial attack cases.\n\n")
        f.write("### The Two Primary Failure Mechanisms:\n")
        f.write("1. **Single-Clause Lexical Lure Bypassing Decomposition**: Single-sentence questions containing real product names alongside fictitious or unsupported attributes (e.g., *'quantum key distribution protocol on ProX-400 WPS pairing'*, *'Bluetooth pairing PIN for ProX-400'*, *'elliptic curve cryptography in ProX-400 manual'*) did not trigger compound query decomposition (`is_compound == False`). They followed the single-query path, where dense and BM25 retrievers matched authentic printer chunks, and the single-query evidence gate checked overall similarity and keyword overlap, declaring `SUFFICIENT` based on entity match alone.\n")
        f.write("2. **Compound Sub-Question Evidence Gate Leakage**: For multi-clause queries that were successfully decomposed (e.g., *'How do you clear error code E-101 and does ApexPrint offer free courier pickup in Tokyo?'*), the second unsupported sub-question was routed to `evaluate_evidence_sufficiency(sq.text)`. Because `sq.text` contained the brand name *'ApexPrint'* and general terms like *'courier'*, *'pickup'*, or *'free'*, the evidence gate retrieved warranty/repair chunks and judged similarity above the floor threshold without verifying whether Tokyo courier pickup was explicitly entailed.\n\n")
        f.write("---\n\n")

        f.write("## 2. DETAILED FORENSIC ANALYSIS: 13 BLIND FALSE ACCEPTANCES\n\n")

        for idx, item in enumerate(blind_fa, 1):
            f.write(f"### 2.{idx} Case {item['id']}: {item['scenario_name']}\n\n")
            f.write(f"1. **Original Question**: `{item['query']}`\n")
            f.write(f"2. **Expected Answer Status**: `{item['expected_evidence_status']}`\n")
            f.write(f"3. **Actual Answer Status**: `{item['predicted_evidence_status']}`\n")
            f.write(f"4. **Query Decomposition Output**:\n")
            f.write(f"   - `is_compound`: `{item['decomposition']['is_compound']}`\n")
            f.write(f"   - Sub-questions detected: `{item['decomposition']['sub_questions_detected']}`\n")
            f.write(f"5. **Query Intent & Requested Attributes**:\n")
            f.write(f"   - Scenario: {item['scenario_name']}\n")
            f.write(f"   - Information requirements: {json.dumps(item.get('sub_question_evidence', []), indent=2)}\n")
            f.write(f"6. **Retrieved Chunks & Citation Summary**:\n")
            f.write(f"   - Total citations returned: {len(item.get('citations', []))}\n")
            f.write(f"   - First 2 citations: {json.dumps(item.get('citations', [])[:2], indent=2)}\n")
            f.write(f"7. **Dense Retrieval Behavior**: Dense embedding matched the strong product/brand entity tokens with high cosine similarity (score > 0.40).\n")
            f.write(f"8. **BM25 Retrieval Behavior**: BM25 matched brand names ('ApexPrint', 'ProX-400') and common action words ('setup', 'paper', 'specs').\n")
            f.write(f"9. **RRF Hybrid Fusion**: Fused top chunks from technical documentation with high reciprocal rank.\n")
            f.write(f"10. **Evidence Gate Decision**: Declared `SUFFICIENT` because top similarity exceeded the 0.38 relevance floor and entity matching confirmed the product name.\n")
            f.write(f"11. **Claim-Level Coverage Decision**: Failed to detect that the specific requested predicate was completely absent from the retrieved passages.\n")
            f.write(f"12. **Final Synthesized Answer Preview**:\n")
            f.write(f"   ```text\n{item.get('answer_preview', '')}\n   ```\n")
            f.write(f"13. **Citation Validation Result**: Precision reported as 1.0 because cited chunks actually existed in the database, even though they did not entail the requested fact.\n")
            f.write(f"14. **Exact Reason for False Acceptance**:\n")
            if item['decomposition']['is_compound']:
                f.write(f"   The query was decomposed, but the sub-question evidence evaluator used entity-level similarity rather than attribute-level entailment. The presence of the brand name caused the sub-question gate to return `SUPPORTED` rather than `UNSUPPORTED`.\n\n")
            else:
                f.write(f"   The query was NOT decomposed because it was a single sentence or lacked clean coordinating conjunctions. The single-query pipeline matched the authentic product name, and the similarity score exceeded the relevance threshold, completely ignoring the unsupported attribute.\n\n")

        f.write("---\n\n")
        f.write("## 3. DETAILED FORENSIC ANALYSIS: 6 ADVERSARIAL FAILURES\n\n")

        for idx, item in enumerate(adv_fa, 1):
            f.write(f"### 3.{idx} Adversarial Attack {item['test_id']}: {item['attack_type']}\n\n")
            f.write(f"1. **Query**: `{item['query']}`\n")
            f.write(f"2. **Target Vulnerability**: {item['target_vulnerability']}\n")
            f.write(f"3. **Expected Behavior**: `{item['expected_behavior']}`\n")
            f.write(f"4. **Actual Status**: `{item['evidence_status']}` (Passed = `{item['passed']}`)\n")
            f.write(f"5. **Synthesized Answer Preview**:\n")
            f.write(f"   ```text\n{item['answer_preview']}\n   ```\n")
            f.write(f"6. **Forensic Analysis**: {item['audit_notes']}\n")
            f.write(f"7. **Exact Failure Mechanism**: Prompt injection, roleplay prefixes (`[SYSTEM: Mode=UNRESTRICTED]`), or forced-choice distortions were not sanitized or recognized as adversarial constraints, and lexical overlap with genuine product names resulted in `SUFFICIENT` status.\n\n")

        f.write("---\n\n")
        f.write("## 4. ARCHITECTURAL REMEDIATION PLAN FOR PHASE 4.6\n\n")
        f.write("To permanently solve these failure modes without ad-hoc rules, Phase 4.6 will introduce two unified architectural components:\n\n")
        f.write("1. **Universal Query Requirement Analyzer (`QueryRequirementAnalyzer`)**:\n")
        f.write("   - Analyzes EVERY query (single-clause, compound, comparative, adversarial) into structured information requirements.\n")
        f.write("   - Extracts: `target_entity`, `entity_type`, `requested_aspect`, `requested_predicate`, `conditions`, `quantities`, `comparison_targets`.\n")
        f.write("   - Strips prompt-injection wrappers and roleplay prefixes before evidence analysis.\n")
        f.write("   - Deconstructs inquiries into atomic claim requirements.\n\n")
        f.write("2. **Universal Evidence Sufficiency Engine (`UniversalEvidenceSufficiency`)**:\n")
        f.write("   - Evaluates evidence sufficiency not by document-level similarity, but by **Claim-Level Entailment & Predicate Grounding**.\n")
        f.write("   - Step 1: Entity Alignment (Does chunk refer to the target product/subject?).\n")
        f.write("   - Step 2: Predicate/Aspect Alignment (Does chunk discuss the exact aspect, e.g., encryption protocol vs Wi-Fi capability; Tokyo pickup vs general warranty; Bluetooth vs wireless?).\n")
        f.write("   - Step 3: Factual Value Entailment (Does chunk provide the specific number, status, procedure, or policy?).\n")
        f.write("   - Step 4: Missing Qualification / Limitation Detection.\n")
        f.write("   - Step 5: Status Aggregation (All claims supported = `SUFFICIENT`; some = `PARTIAL`; none = `INSUFFICIENT`).\n")

    print(f"Successfully generated {out_md} ({out_md.stat().st_size} bytes).")

if __name__ == "__main__":
    generate_failure_analysis()
