"""Stage 8 Phase 4.3 Master Evaluation Runner.

Executes complete re-evaluation across all 92 queries:
1. Original Phase 4 Benchmark (50 questions)
2. Phase 4.1 Regression Benchmark (10 questions)
3. Phase 4.2 Independent Validation Benchmark (32 questions)

Generates:
- evaluations/stage8_phase4_3/phase4_3_evaluation_results.json
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
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
OUTPUT_DIR = PROJECT_ROOT / "evaluations" / "stage8_phase4_3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def compute_dataset_metrics(results: List[Dict[str, Any]], label_override: Dict[str, str] = None) -> Dict[str, Any]:
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
        qid = r["id"]
        exp = label_override.get(qid, r["expected_status"]) if label_override else r["expected_status"]
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
    total_correct = correct_sufficient + correct_partial + correct_insufficient + correct_conflicting
    accuracy = round(total_correct / len(results), 4)

    return {
        "total_evaluated": len(results),
        "supported_query_count": supported_total,
        "unsupported_query_count": unsupported_total,
        "correct_sufficient_count": correct_sufficient,
        "correct_partial_count": correct_partial,
        "correct_insufficient_count": correct_insufficient,
        "correct_conflicting_count": correct_conflicting,
        "total_correct": total_correct,
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
    print("STAGE 8 PHASE 4.3: MASTER EVALUATION RE-RUN (92 QUERIES)")
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
        print(f"  [P4 {idx:02d}/50] {qid}: Exp={exp_status:<12} | Act={resp.evidence_status:<12} | Gate={g_ms:4.1f}ms | Tot={tot_ms:5.1f}ms | Verdict={record['verdict']}")

    p4_metrics = compute_dataset_metrics(results_p4)

    # ---------------------------------------------------------
    # B. Phase 4.1 Regression Benchmark (10 Questions)
    # ---------------------------------------------------------
    print("\n[B] Evaluating Phase 4.1 Regression Benchmark (10 Questions)...")
    results_reg = []
    latencies_reg_tot = []
    latencies_reg_gate = []

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
        latencies_reg_gate.append(g_ms)
        if resp.evidence_status in ["INSUFFICIENT", "CONFLICTING"]:
            latencies_p4_abstained.append(tot_ms)
        else:
            latencies_p4_supported.append(tot_ms)

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
            latencies_p4_abstained.append(tot_ms)
        else:
            latencies_p4_supported.append(tot_ms)

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

    val_metrics_original_labels = compute_dataset_metrics(results_val)

    # Audited label corrections for independent dataset:
    # P4_2_VAL21: expected SUFFICIENT (manual and warranty agree on prohibition)
    # P4_2_VAL22: expected INSUFFICIENT (bypassing is undocumented/hazardous)
    audited_label_overrides = {
        "P4_2_VAL21": "SUFFICIENT",
        "P4_2_VAL22": "INSUFFICIENT",
    }
    val_metrics_audited_labels = compute_dataset_metrics(results_val, label_override=audited_label_overrides)

    # ---------------------------------------------------------
    # D. Combined Suite Metrics (92 Questions)
    # ---------------------------------------------------------
    all_results = results_p4 + results_reg + results_val
    combined_metrics_original_labels = compute_dataset_metrics(all_results)
    combined_metrics_audited_labels = compute_dataset_metrics(all_results, label_override=audited_label_overrides)

    # Latency Profiling
    all_gate_latencies = latencies_p4_gate + latencies_reg_gate + latencies_val_gate
    all_tot_latencies = latencies_p4_tot + latencies_reg_tot + latencies_val_tot

    latency_profile = {
        "metadata": {
            "active_generation_provider": "local_grounded_synthesizer (Local deterministic execution)",
            "retrieval_mode": "hybrid_mcp (ChromaDB + BM25 + RRF)",
            "total_queries_evaluated": len(all_results),
        },
        "execution_paths": {
            "evidence_gate_overhead": compute_latency_stats(all_gate_latencies),
            "warm_hybrid_retrieval": compute_latency_stats(latencies_p4_ret),
            "local_synthesis_generation": compute_latency_stats(latencies_p4_gen),
            "end_to_end_supported_path": compute_latency_stats(latencies_p4_supported),
            "end_to_end_abstention_path": compute_latency_stats(latencies_p4_abstained),
            "full_query_latency_overall": compute_latency_stats(all_tot_latencies),
        },
    }

    # Consolidated Master Results Artifact
    master_artifact = {
        "metadata": {
            "evaluation_phase": "Stage 8 Phase 4.3 Master Evaluation Re-Run",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_queries_evaluated": 92,
            "architecture": "RAG + MCP + EvidenceGate Hardening",
            "evidence_gate_similarity_floor": 0.2800,
        },
        "benchmarks": {
            "original_50_benchmark": {
                "dataset_name": "Original Phase 4 Benchmark (50 Questions)",
                "summary_metrics": p4_metrics,
                "detailed_results": results_p4,
            },
            "phase4_1_regression_benchmark": {
                "dataset_name": "Phase 4.1 Regression Benchmark (10 Questions)",
                "summary_metrics": reg_metrics,
                "detailed_results": results_reg,
            },
            "independent_validation_benchmark": {
                "dataset_name": "Phase 4.2 Independent Validation Benchmark (32 Questions)",
                "summary_metrics_original_labels": val_metrics_original_labels,
                "summary_metrics_audited_labels": val_metrics_audited_labels,
                "detailed_results": results_val,
            },
            "combined_suite_92_queries": {
                "dataset_name": "Combined Master Evaluation Suite (92 Questions)",
                "summary_metrics_original_labels": combined_metrics_original_labels,
                "summary_metrics_audited_labels": combined_metrics_audited_labels,
            },
        },
        "latency_profile": latency_profile,
    }

    output_path = OUTPUT_DIR / "phase4_3_evaluation_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(master_artifact, f, indent=2)

    print("\n" + "=" * 80)
    print("MASTER EVALUATION RE-RUN COMPLETE")
    print(f"Results written to: {output_path}")
    print("=" * 80)
    print(f"P4 (50): Accuracy={p4_metrics['overall_accuracy']*100:.1f}% | Supported={p4_metrics['correct_sufficient_count']}/{p4_metrics['supported_query_count']} | FAR={p4_metrics['false_acceptance_rate_on_ood']*100:.1f}% | FRR={p4_metrics['false_rejection_rate_on_supported']*100:.1f}%")
    print(f"Reg (10): Accuracy={reg_metrics['overall_accuracy']*100:.1f}% | Total Correct={reg_metrics['total_correct']}/10")
    print(f"Val (32) [Orig Labels]: Accuracy={val_metrics_original_labels['overall_accuracy']*100:.1f}% | Total Correct={val_metrics_original_labels['total_correct']}/32 | FAR={val_metrics_original_labels['false_acceptance_rate_on_ood']*100:.1f}%")
    print(f"Val (32) [Audited]:    Accuracy={val_metrics_audited_labels['overall_accuracy']*100:.1f}% | Total Correct={val_metrics_audited_labels['total_correct']}/32 | FAR={val_metrics_audited_labels['false_acceptance_rate_on_ood']*100:.1f}%")
    print(f"Combined (92) [Orig]:   Accuracy={combined_metrics_original_labels['overall_accuracy']*100:.1f}% | Total Correct={combined_metrics_original_labels['total_correct']}/92")
    print(f"Combined (92) [Audited]: Accuracy={combined_metrics_audited_labels['overall_accuracy']*100:.1f}% | Total Correct={combined_metrics_audited_labels['total_correct']}/92")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
