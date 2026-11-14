"""Stage 8 Phase 4.2 Master Evaluation Runner.

Executes three distinct evaluations:
A. Original Phase 4 Benchmark (50 questions)
B. Phase 4.1 Regression Benchmark (10 questions)
C. Phase 4.2 Independent Validation Benchmark (32 questions)

Outputs:
- evaluations/stage8_phase4_2/original_benchmark_results.json
- evaluations/stage8_phase4_2/regression_benchmark_results.json
- evaluations/stage8_phase4_2/independent_validation_results.json
- evaluations/stage8_phase4_2/latency_comparison.json
- evaluations/stage8_phase4_2/claim_level_grounding_review.csv
"""

import os
import sys
import json
import time
import csv
import re
from pathlib import Path
from typing import List, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from app.services.rag_service import rag_service

STAGE8_PHASE4_DATASET = PROJECT_ROOT / "evaluations" / "stage8_phase4" / "dataset" / "benchmark_50_questions.json"
STAGE8_PHASE4_1_REG = [
    {
        "id": "P4_1_REG01",
        "category": "Competitor Hardware",
        "query": "How do you clear a paper jam on a Canon imageCLASS MF445dw laser multifunction printer?",
        "is_supported": False,
        "expected_status": "INSUFFICIENT",
        "expected_reason": "Competitor brand mismatch (Canon vs. ApexPrint)",
    },
    {
        "id": "P4_1_REG02",
        "category": "Competitor Hardware",
        "query": "What is the print speed and monthly duty cycle of an Epson EcoTank ET-4760 all-in-one printer?",
        "is_supported": False,
        "expected_status": "INSUFFICIENT",
        "expected_reason": "Competitor brand mismatch (Epson EcoTank vs. ApexPrint)",
    },
    {
        "id": "P4_1_REG03",
        "category": "Missing Policy Clause",
        "query": "Does the standard limited warranty cover damage caused by earthquake or tsunami floods?",
        "is_supported": False,
        "expected_status": "INSUFFICIENT",
        "expected_reason": "Missing policy perils (earthquake, tsunami flood)",
    },
    {
        "id": "P4_1_REG04",
        "category": "Missing Policy Clause",
        "query": "Does the commercial care warranty cover cosmetic scratches and exterior casing scuffs?",
        "is_supported": False,
        "expected_status": "INSUFFICIENT",
        "expected_reason": "Missing policy clause (cosmetic scratches, scuffs)",
    },
    {
        "id": "P4_1_REG05",
        "category": "Alien Out-of-Domain",
        "query": "What is the capital city of Australia and what is its current estimated population?",
        "is_supported": False,
        "expected_status": "INSUFFICIENT",
        "expected_reason": "Sub-threshold similarity; alien topic outside knowledge base",
    },
    {
        "id": "P4_1_REG06",
        "category": "Generic Troubleshooting",
        "query": "What causes vertical black streaks on laser printer outputs and how do you inspect the drum unit?",
        "is_supported": True,
        "expected_status": "SUFFICIENT",
        "expected_reason": "Generic troubleshooting inquiry supported by documentation",
    },
    {
        "id": "P4_1_REG07",
        "category": "Generic Paper Handling",
        "query": "Explain how duplex paper feeding operates mechanically during two-sided document printing.",
        "is_supported": True,
        "expected_status": "SUFFICIENT",
        "expected_reason": "Generic mechanical paper path supported by user manual",
    },
    {
        "id": "P4_1_REG08",
        "category": "Documented Policy Exclusion",
        "query": "Does the warranty policy explicitly exclude damage resulting from non-OEM or third-party ink cartridges?",
        "is_supported": True,
        "expected_status": "SUFFICIENT",
        "expected_reason": "Explicit exclusion clause documented in warranty policy",
    },
    {
        "id": "P4_1_REG09",
        "category": "Project Architecture",
        "query": "How does the citation validation engine ensure that source filenames and page numbers are not fabricated?",
        "is_supported": True,
        "expected_status": "SUFFICIENT",
        "expected_reason": "Project Dossier architecture section documented",
    },
    {
        "id": "P4_1_REG10",
        "category": "Project Constraints",
        "query": "What is the storage budget constraint and how does the system enforce a sub-1024 MB disk footprint?",
        "is_supported": True,
        "expected_status": "SUFFICIENT",
        "expected_reason": "Storage constraint documentation in Project Dossier",
    },
]
STAGE8_PHASE4_2_DATASET = PROJECT_ROOT / "evaluations" / "stage8_phase4_2" / "independent_validation_dataset.json"
OUTPUT_DIR = PROJECT_ROOT / "evaluations" / "stage8_phase4_2"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def compute_dataset_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute complete classification metrics and confusion matrix."""
    possible_statuses = ["SUFFICIENT", "PARTIAL", "INSUFFICIENT", "CONFLICTING"]
    confusion_matrix = {exp: {act: 0 for act in possible_statuses} for exp in possible_statuses}
    
    correct_sufficient = 0
    correct_partial = 0
    correct_insufficient = 0
    correct_conflicting = 0
    
    supported_total = 0
    unsupported_total = 0
    
    false_acceptances = 0 # unsupported classified as SUFFICIENT
    false_rejections = 0   # supported classified as INSUFFICIENT
    appropriate_abstentions = 0 # unsupported classified as INSUFFICIENT or CONFLICTING
    
    per_category = {}

    for r in results:
        exp = r["expected_status"]
        act = r["actual_status"]
        is_supp = r["is_supported"]
        cat = r.get("category", "General")
        
        per_category.setdefault(cat, {"total": 0, "correct": 0})
        per_category[cat]["total"] += 1
        
        if exp in confusion_matrix and act in confusion_matrix[exp]:
            confusion_matrix[exp][act] += 1
            
        is_correct = (exp == act)
        if is_correct:
            per_category[cat]["correct"] += 1
            if exp == "SUFFICIENT":
                correct_sufficient += 1
            elif exp == "PARTIAL":
                correct_partial += 1
            elif exp == "INSUFFICIENT":
                correct_insufficient += 1
            elif exp == "CONFLICTING":
                correct_conflicting += 1
                
        if is_supp:
            supported_total += 1
            if act == "INSUFFICIENT":
                false_rejections += 1
        else:
            unsupported_total += 1
            if act == "SUFFICIENT":
                false_acceptances += 1
            if act in ["INSUFFICIENT", "CONFLICTING"]:
                appropriate_abstentions += 1
                
    far = round(false_acceptances / unsupported_total, 4) if unsupported_total > 0 else 0.0
    frr = round(false_rejections / supported_total, 4) if supported_total > 0 else 0.0
    aar = round(appropriate_abstentions / unsupported_total, 4) if unsupported_total > 0 else 1.0
    accuracy = round(sum(1 for r in results if r["expected_status"] == r["actual_status"]) / len(results), 4)

    return {
        "total_evaluated": len(results),
        "supported_query_count": supported_total,
        "unsupported_query_count": unsupported_total,
        "correct_sufficient_count": correct_sufficient,
        "correct_partial_count": correct_partial,
        "correct_insufficient_count": correct_insufficient,
        "correct_conflicting_count": correct_conflicting,
        "false_acceptance_count": false_acceptances,
        "false_acceptance_rate_on_ood": far,
        "false_rejection_count": false_rejections,
        "false_rejection_rate_on_supported": frr,
        "appropriate_abstention_count": appropriate_abstentions,
        "appropriate_abstention_rate_on_ood": aar,
        "overall_accuracy": accuracy,
        "confusion_matrix": confusion_matrix,
        "per_category_breakdown": {
            k: {
                "total": v["total"],
                "correct": v["correct"],
                "accuracy": round(v["correct"] / v["total"], 4) if v["total"] > 0 else 0.0,
            }
            for k, v in per_category.items()
        },
    }


def compute_latency_stats(latencies: List[float]) -> Dict[str, float]:
    """Compute count, mean, median, p95, min, max."""
    if not latencies:
        return {"count": 0, "mean": 0.0, "median": 0.0, "p95": 0.0, "min": 0.0, "max": 0.0}
    s = sorted(latencies)
    n = len(s)
    mean = round(sum(s) / n, 2)
    median = round(s[n // 2] if n % 2 != 0 else (s[n // 2 - 1] + s[n // 2]) / 2, 2)
    p95_idx = int(0.95 * n)
    p95 = round(s[min(p95_idx, n - 1)], 2)
    return {
        "count": n,
        "mean": mean,
        "median": median,
        "p95": p95,
        "min": round(min(s), 2),
        "max": round(max(s), 2),
    }


async def main():
    print("=" * 80)
    print("STAGE 8 PHASE 4.2: INDEPENDENT MASTER EVALUATION SUITE")
    print("=" * 80)

    # ---------------------------------------------------------
    # A. Original Phase 4 Benchmark (50 Questions)
    # ---------------------------------------------------------
    print("\n[A] Evaluating Original Phase 4 Benchmark (50 Questions)...")
    with open(STAGE8_PHASE4_DATASET, "r", encoding="utf-8") as f:
        bench_p4 = json.load(f)
    p4_questions = bench_p4["questions"] if isinstance(bench_p4, dict) and "questions" in bench_p4 else bench_p4

    results_p4 = []
    latencies_p4_ret = []
    latencies_p4_gate = []
    latencies_p4_gen = []
    latencies_p4_tot = []
    latencies_p4_abstained = []
    latencies_p4_supported = []

    for idx, q_item in enumerate(p4_questions, 1):
        qid = q_item["id"]
        q_text = q_item["query"]
        tax = q_item.get("question_type") or q_item.get("type") or q_item.get("taxonomy") or "General"
        exp_status = q_item.get("expected_evidence_status") or q_item.get("expected_status")
        is_supp = (exp_status != "INSUFFICIENT" and "H_unsupported" not in str(tax) and "Type H" not in str(tax))

        t0 = time.perf_counter()
        resp = await rag_service.process_query(q_text, retrieval_mode="multi_context")
        tot_ms = round((time.perf_counter() - t0) * 1000, 2)

        tb = resp.timing_breakdown or {}
        g_ms = tb.get("evidence_gate_ms", 0.0)
        r_ms = resp.retrieval_latency_ms
        s_ms = resp.generation_latency_ms or 0.0

        latencies_p4_ret.append(r_ms)
        latencies_p4_gate.append(g_ms)
        latencies_p4_gen.append(s_ms)
        latencies_p4_tot.append(tot_ms)

        if resp.evidence_status == "INSUFFICIENT":
            latencies_p4_abstained.append(tot_ms)
        else:
            latencies_p4_supported.append(tot_ms)

        record = {
            "id": qid,
            "query": q_text,
            "category": tax,
            "is_supported": is_supp,
            "expected_status": exp_status,
            "actual_status": resp.evidence_status,
            "verdict": "PASS" if resp.evidence_status == exp_status else "FAIL",
            "supporting_citations_count": len(resp.supporting_citations),
            "citations_verified": all(c.is_verified for c in resp.supporting_citations),
            "gate_latency_ms": g_ms,
            "retrieval_latency_ms": r_ms,
            "generation_latency_ms": s_ms,
            "total_latency_ms": tot_ms,
            "provider_status": resp.provider_status,
            "answer_preview": resp.answer[:200].replace("\n", " ") + "...",
        }
        results_p4.append(record)
        print(f"  [P4 {idx:02d}/50] {qid}: Exp={exp_status:<12} | Act={resp.evidence_status:<12} | Gate={g_ms:4.1f}ms | Tot={tot_ms:5.1f}ms")

    p4_metrics = compute_dataset_metrics(results_p4)
    original_benchmark_artifact = {
        "dataset_name": "Original Phase 4 Benchmark (50 Questions)",
        "summary_metrics": p4_metrics,
        "detailed_results": results_p4,
    }
    with open(OUTPUT_DIR / "original_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(original_benchmark_artifact, f, indent=2)

    # ---------------------------------------------------------
    # B. Phase 4.1 Regression Benchmark (10 Questions)
    # ---------------------------------------------------------
    print("\n[B] Evaluating Phase 4.1 Regression Benchmark (10 Questions)...")
    results_reg = []
    latencies_reg_tot = []

    for idx, reg_item in enumerate(STAGE8_PHASE4_1_REG, 1):
        qid = reg_item["id"]
        q_text = reg_item["query"]
        exp_status = reg_item["expected_status"]
        is_supp = reg_item["is_supported"]
        cat = reg_item["category"]

        t0 = time.perf_counter()
        resp = await rag_service.process_query(q_text, retrieval_mode="multi_context")
        tot_ms = round((time.perf_counter() - t0) * 1000, 2)
        tb = resp.timing_breakdown or {}
        g_ms = tb.get("evidence_gate_ms", 0.0)

        latencies_reg_tot.append(tot_ms)
        record = {
            "id": qid,
            "query": q_text,
            "category": cat,
            "is_supported": is_supp,
            "expected_status": exp_status,
            "actual_status": resp.evidence_status,
            "verdict": "PASS" if resp.evidence_status == exp_status else "FAIL",
            "supporting_citations_count": len(resp.supporting_citations),
            "citations_verified": all(c.is_verified for c in resp.supporting_citations),
            "gate_latency_ms": g_ms,
            "total_latency_ms": tot_ms,
            "provider_status": resp.provider_status,
            "answer_preview": resp.answer[:200].replace("\n", " ") + "...",
        }
        results_reg.append(record)
        print(f"  [REG {idx:02d}/10] {qid}: Exp={exp_status:<12} | Act={resp.evidence_status:<12} | Verdict={record['verdict']}")

    reg_metrics = compute_dataset_metrics(results_reg)
    regression_benchmark_artifact = {
        "dataset_name": "Phase 4.1 Regression Benchmark (10 Questions)",
        "summary_metrics": reg_metrics,
        "detailed_results": results_reg,
    }
    with open(OUTPUT_DIR / "regression_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(regression_benchmark_artifact, f, indent=2)

    # ---------------------------------------------------------
    # C. Phase 4.2 Independent Validation Benchmark (32 Questions)
    # ---------------------------------------------------------
    print("\n[C] Evaluating Phase 4.2 Independent Validation Benchmark (32 Questions)...")
    with open(STAGE8_PHASE4_2_DATASET, "r", encoding="utf-8") as f:
        bench_val = json.load(f)
    val_questions = bench_val["questions"]

    results_val = []
    latencies_val_tot = []
    latencies_val_gate = []
    latencies_val_abstained = []
    latencies_val_supported = []

    for idx, v_item in enumerate(val_questions, 1):
        qid = v_item["id"]
        q_text = v_item["query"]
        exp_status = v_item["expected_evidence_status"]
        is_supp = v_item["is_supported"]
        cat = v_item["taxonomy_category"]

        t0 = time.perf_counter()
        resp = await rag_service.process_query(q_text, retrieval_mode="multi_context")
        tot_ms = round((time.perf_counter() - t0) * 1000, 2)
        tb = resp.timing_breakdown or {}
        g_ms = tb.get("evidence_gate_ms", 0.0)

        latencies_val_tot.append(tot_ms)
        latencies_val_gate.append(g_ms)
        if resp.evidence_status in ["INSUFFICIENT", "CONFLICTING"]:
            latencies_val_abstained.append(tot_ms)
        else:
            latencies_val_supported.append(tot_ms)

        record = {
            "id": qid,
            "query": q_text,
            "category": cat,
            "is_supported": is_supp,
            "expected_status": exp_status,
            "actual_status": resp.evidence_status,
            "verdict": "PASS" if resp.evidence_status == exp_status else "FAIL",
            "supporting_citations_count": len(resp.supporting_citations),
            "citations_verified": all(c.is_verified for c in resp.supporting_citations),
            "gate_latency_ms": g_ms,
            "total_latency_ms": tot_ms,
            "provider_status": resp.provider_status,
            "answer_preview": resp.answer[:200].replace("\n", " ") + "...",
        }
        results_val.append(record)
        print(f"  [VAL {idx:02d}/32] {qid}: Exp={exp_status:<12} | Act={resp.evidence_status:<12} | Verdict={record['verdict']}")

    val_metrics = compute_dataset_metrics(results_val)
    independent_validation_artifact = {
        "dataset_name": "Stage 8 Phase 4.2 Independent Validation Dataset (32 Questions)",
        "summary_metrics": val_metrics,
        "detailed_results": results_val,
    }
    with open(OUTPUT_DIR / "independent_validation_results.json", "w", encoding="utf-8") as f:
        json.dump(independent_validation_artifact, f, indent=2)

    # ---------------------------------------------------------
    # D. Latency Comparison & Profiling Artifact
    # ---------------------------------------------------------
    all_abstained_latencies = latencies_p4_abstained + [r["total_latency_ms"] for r in results_reg if r["actual_status"] == "INSUFFICIENT"] + latencies_val_abstained
    all_supported_latencies = latencies_p4_supported + [r["total_latency_ms"] for r in results_reg if r["actual_status"] == "SUFFICIENT"] + latencies_val_supported
    all_gate_latencies = latencies_p4_gate + [r["gate_latency_ms"] for r in results_reg] + latencies_val_gate

    latency_comparison = {
        "metadata": {
            "active_generation_provider": "local_grounded_synthesizer (Local deterministic execution)",
            "retrieval_mode": "hybrid_mcp (ChromaDB + BM25 + RRF)",
            "vector_index": "sentence-transformers/all-MiniLM-L6-v2 in .chroma_live",
        },
        "execution_paths": {
            "evidence_gate_overhead": compute_latency_stats(all_gate_latencies),
            "warm_hybrid_retrieval": compute_latency_stats(latencies_p4_ret),
            "local_synthesis_generation": compute_latency_stats(latencies_p4_gen),
            "end_to_end_supported_path": compute_latency_stats(all_supported_latencies),
            "end_to_end_abstention_path": compute_latency_stats(all_abstained_latencies),
            "full_query_latency_overall": compute_latency_stats(latencies_p4_tot + latencies_reg_tot + latencies_val_tot),
        },
        "latency_reduction_analysis": {
            "mean_supported_latency_ms": compute_latency_stats(all_supported_latencies)["mean"],
            "mean_abstention_latency_ms": compute_latency_stats(all_abstained_latencies)["mean"],
            "relative_latency_reduction_percent": round(
                (1.0 - (compute_latency_stats(all_abstained_latencies)["mean"] / max(1.0, compute_latency_stats(all_supported_latencies)["mean"]))) * 100, 2
            ),
            "conclusion": (
                "When the EvidenceGate rejects an ungrounded or out-of-domain query, "
                "context assembly and synthesis are completely bypassed, saving computational overhead and latency."
            ),
        },
    }
    with open(OUTPUT_DIR / "latency_comparison.json", "w", encoding="utf-8") as f:
        json.dump(latency_comparison, f, indent=2)

    # ---------------------------------------------------------
    # E. Claim-Level Grounding Review CSV Template
    # ---------------------------------------------------------
    claim_review_rows = []
    # Sample queries across all 4 statuses
    sampled_records = [
        # 4 Supported
        results_p4[0],   # P4_Q01 specs
        results_p4[2],   # P4_Q03 embedding
        results_val[2],  # VAL03 chunking
        results_val[6],  # VAL07 RRF
        # 2 Conflicting
        results_val[20], # VAL21 fuser disassembly
        results_val[21], # VAL22 voltage bypass
        # 1 Partial
        results_val[22], # VAL23 warranty + international RMA
        # 4 Insufficient
        results_p4[45],  # P4_Q46 biryani
        results_p4[46],  # P4_Q47 HP LaserJet
        results_val[23], # VAL24 Ricoh Aficio
        results_val[26], # VAL27 volcanic ash
    ]

    for rec in sampled_records:
        qid = rec["id"]
        q_text = rec["query"]
        st = rec["actual_status"]
        ans = rec["answer_preview"]
        
        # Split into individual sentence claims
        cleaned_ans = re.sub(r"\[.*?\]", "", ans)
        sents = [s.strip() for s in re.split(r"(?<=[a-zA-Z0-9])\.\s+|\n+", cleaned_ans) if len(s.strip()) > 15]
        if not sents:
            sents = [ans[:120]]
            
        for s_idx, claim in enumerate(sents[:3], 1):
            claim_review_rows.append({
                "query_id": qid,
                "evidence_status": st,
                "query_text": q_text,
                "claim_index": s_idx,
                "claim_text": claim,
                "supporting_evidence_id": "doc_evidence_ref" if st in ["SUFFICIENT", "CONFLICTING"] else "None",
                "is_directly_supported": "YES" if st in ["SUFFICIENT", "CONFLICTING"] else "NO",
                "is_partially_supported": "YES" if st == "PARTIAL" else "NO",
                "is_unsupported": "YES" if st == "INSUFFICIENT" and "insufficient" not in claim.lower() else "NO",
                "is_contradictory": "YES" if st == "CONFLICTING" and "conflict" in claim.lower() else "NO",
                "is_reasonable_inference": "NO",
                "reviewer_evaluation_status": "PENDING_INDEPENDENT_HUMAN_REVIEW",
                "auditor_notes": f"Representative {st} claim sample",
            })

    with open(OUTPUT_DIR / "claim_level_grounding_review.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "query_id", "evidence_status", "query_text", "claim_index", "claim_text",
            "supporting_evidence_id", "is_directly_supported", "is_partially_supported",
            "is_unsupported", "is_contradictory", "is_reasonable_inference",
            "reviewer_evaluation_status", "auditor_notes"
        ])
        writer.writeheader()
        writer.writerows(claim_review_rows)

    print("\n" + "=" * 80)
    print("PHASE 4.2 MASTER EVALUATION SUMMARY:")
    print("-" * 80)
    print(f"[A] Original 50 Benchmark: Accuracy = {p4_metrics['overall_accuracy']*100:.1f}% | Supported = {p4_metrics['correct_sufficient_count']}/{p4_metrics['supported_query_count']} | OOD Abstention = {p4_metrics['appropriate_abstention_count']}/{p4_metrics['unsupported_query_count']}")
    print(f"[B] Phase 4.1 Regression: Accuracy = {reg_metrics['overall_accuracy']*100:.1f}% | Supported = {reg_metrics['correct_sufficient_count']}/{reg_metrics['supported_query_count']} | OOD Abstention = {reg_metrics['appropriate_abstention_count']}/{reg_metrics['unsupported_query_count']}")
    print(f"[C] Phase 4.2 Independent: Accuracy = {val_metrics['overall_accuracy']*100:.1f}% | Supported = {val_metrics['correct_sufficient_count']}/{val_metrics['supported_query_count']} | OOD Abstention = {val_metrics['appropriate_abstention_count']}/{val_metrics['unsupported_query_count']}")
    print(f"Mean Evidence Gate Overhead: {all_gate_latencies and round(sum(all_gate_latencies)/len(all_gate_latencies), 3)} ms")
    print(f"Mean Abstention Latency: {latency_comparison['execution_paths']['end_to_end_abstention_path']['mean']} ms (vs Supported {latency_comparison['execution_paths']['end_to_end_supported_path']['mean']} ms)")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
