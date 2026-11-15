"""Audit and recompute all evaluation metrics from raw JSON results."""

import json
from pathlib import Path
from collections import Counter

P4_PATH = Path("evaluations/stage8_phase4_2/original_benchmark_results.json")
REG_PATH = Path("evaluations/stage8_phase4_2/regression_benchmark_results.json")
VAL_PATH = Path("evaluations/stage8_phase4_2/independent_validation_results.json")
VAL_DATASET_PATH = Path("evaluations/stage8_phase4_2/independent_validation_dataset.json")

def audit_dataset(name, path):
    data = json.load(open(path, encoding="utf-8"))
    summary = data.get("summary_metrics", {})
    results = data.get("detailed_results", [])
    
    print(f"\n==========================================")
    print(f"AUDITING: {name} ({len(results)} items)")
    print(f"==========================================")
    print("Reported in summary_metrics:")
    for k, v in summary.items():
        if k != "confusion_matrix" and k != "per_category_breakdown":
            print(f"  {k}: {v}")
            
    print("\nConfusion Matrix in summary_metrics:")
    print(json.dumps(summary.get("confusion_matrix", {}), indent=2))
    
    # Recomputing from raw items:
    total = len(results)
    exp_counts = Counter(r["expected_status"] for r in results)
    act_counts = Counter(r["actual_status"] for r in results)
    supp_counts = Counter(r["is_supported"] for r in results)
    verdict_counts = Counter(r["verdict"] for r in results)
    
    print(f"\nRecomputed Raw Counts:")
    print(f"  Total: {total}")
    print(f"  Expected Status: {dict(exp_counts)}")
    print(f"  Actual Status: {dict(act_counts)}")
    print(f"  is_supported: {dict(supp_counts)}")
    print(f"  verdict: {dict(verdict_counts)}")
    
    # Exact confusion matrix:
    possible_statuses = ["SUFFICIENT", "PARTIAL", "INSUFFICIENT", "CONFLICTING"]
    raw_cm = {exp: {act: 0 for act in possible_statuses} for exp in possible_statuses}
    for r in results:
        raw_cm[r["expected_status"]][r["actual_status"]] += 1
    print("\nRecomputed Raw Confusion Matrix:")
    print(json.dumps(raw_cm, indent=2))
    
    # Breakdown of discrepancies and definitions
    # Supported queries: r["is_supported"] == True
    supported_qs = [r for r in results if r["is_supported"]]
    unsupported_qs = [r for r in results if not r["is_supported"]]
    
    print(f"\nSupported queries breakdown ({len(supported_qs)} total):")
    supp_act_counts = Counter(r["actual_status"] for r in supported_qs)
    print(f"  Actual status distribution: {dict(supp_act_counts)}")
    supp_exp_counts = Counter(r["expected_status"] for r in supported_qs)
    print(f"  Expected status distribution: {dict(supp_exp_counts)}")
    
    print(f"\nUnsupported queries breakdown ({len(unsupported_qs)} total):")
    unsupp_act_counts = Counter(r["actual_status"] for r in unsupported_qs)
    print(f"  Actual status distribution: {dict(unsupp_act_counts)}")
    unsupp_exp_counts = Counter(r["expected_status"] for r in unsupported_qs)
    print(f"  Expected status distribution: {dict(unsupp_exp_counts)}")
    
    # Check what was counted as 'false rejection' in the code:
    # In run_stage8_phase4_2_evaluations.py:
    # if is_supp:
    #     if act == "INSUFFICIENT":
    #         false_rejections += 1
    code_fr = sum(1 for r in supported_qs if r["actual_status"] == "INSUFFICIENT")
    strict_fr = sum(1 for r in supported_qs if r["actual_status"] != r["expected_status"])
    non_suff_fr = sum(1 for r in supported_qs if r["actual_status"] != "SUFFICIENT")
    print(f"\nFalse Rejections on Supported under different definitions:")
    print(f"  act == 'INSUFFICIENT': {code_fr} / {len(supported_qs)} = {code_fr/len(supported_qs):.4f}")
    print(f"  act != 'SUFFICIENT': {non_suff_fr} / {len(supported_qs)} = {non_suff_fr/len(supported_qs):.4f}")
    print(f"  act != expected_status: {strict_fr} / {len(supported_qs)} = {strict_fr/len(supported_qs):.4f}")

    # False acceptances on unsupported:
    code_fa = sum(1 for r in unsupported_qs if r["actual_status"] == "SUFFICIENT")
    print(f"\nFalse Acceptances on Unsupported (act == 'SUFFICIENT'):")
    print(f"  {code_fa} / {len(unsupported_qs)} = {code_fa/len(unsupported_qs) if unsupported_qs else 0:.4f}")
    
    return {
        "name": name,
        "total": total,
        "supported_total": len(supported_qs),
        "unsupported_total": len(unsupported_qs),
        "exact_matches": verdict_counts.get("PASS", 0),
        "accuracy": verdict_counts.get("PASS", 0) / total,
        "code_fr": code_fr,
        "non_suff_fr": non_suff_fr,
        "strict_fr": strict_fr,
        "code_fa": code_fa,
        "raw_cm": raw_cm,
        "results": results
    }

if __name__ == "__main__":
    r_p4 = audit_dataset("Original Phase 4", P4_PATH)
    r_reg = audit_dataset("Phase 4.1 Regression", REG_PATH)
    r_val = audit_dataset("Phase 4.2 Independent Validation", VAL_PATH)
    
    # Combined analysis
    all_results = r_p4["results"] + r_reg["results"] + r_val["results"]
    total_all = len(all_results)
    pass_all = sum(1 for r in all_results if r["verdict"] == "PASS")
    supp_all = [r for r in all_results if r["is_supported"]]
    unsupp_all = [r for r in all_results if not r["is_supported"]]
    
    print("\n" + "="*50)
    print("COMBINED BENCHMARK AUDIT (92 QUERIES)")
    print("="*50)
    print(f"Total queries: {total_all}")
    print(f"Total PASS (expected == actual): {pass_all} / {total_all} = {pass_all/total_all:.6f} ({pass_all/total_all*100:.2f}%)")
    print(f"Supported queries total: {len(supp_all)}")
    print(f"Unsupported queries total: {len(unsupp_all)}")
    
    fa_all = sum(1 for r in unsupp_all if r["actual_status"] == "SUFFICIENT")
    fr_code_all = sum(1 for r in supp_all if r["actual_status"] == "INSUFFICIENT")
    fr_non_suff_all = sum(1 for r in supp_all if r["actual_status"] != "SUFFICIENT")
    fr_mismatch_all = sum(1 for r in supp_all if r["actual_status"] != r["expected_status"])
    
    print(f"False acceptances (unsupported -> SUFFICIENT): {fa_all} / {len(unsupp_all)} = {fa_all/len(unsupp_all):.4f}")
    print(f"False rejections (supported -> INSUFFICIENT): {fr_code_all} / {len(supp_all)} = {fr_code_all/len(supp_all):.4f}")
    print(f"False rejections (supported -> non-SUFFICIENT): {fr_non_suff_all} / {len(supp_all)} = {fr_non_suff_all/len(supp_all):.4f}")
    print(f"False rejections (supported -> act != exp): {fr_mismatch_all} / {len(supp_all)} = {fr_mismatch_all/len(supp_all):.4f}")
