#!/usr/bin/env python3
"""
Evaluate the Stage 8 Phase 4.6 Blind Held-Out Benchmark (50 questions).
Outputs evaluations/stage8_phase4_6/blind_test_results.json (Deliverable 10).
"""

import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service

async def run_blind_eval():
    blind_path = Path("evaluations/stage8_phase4_6/blind_test_dataset.json")
    with open(blind_path, "r", encoding="utf-8") as f:
        blind_data = json.load(f)

    questions = blind_data["questions"]
    print(f"--- Running Phase 4.6 Blind Held-Out Benchmark ({len(questions)} queries) ---")

    results = []
    correct_count = 0

    # Metrics counters
    single_clause_unsupported_total = 0
    single_clause_false_acceptances = 0

    compound_nonsufficient_total = 0
    compound_false_acceptances = 0

    supported_total = 0
    false_rejections = 0

    for i, q in enumerate(questions, 1):
        q_id = q["id"]
        query_text = q["query"]
        category = q.get("category", "")
        expected_status = q["expected_status"]

        t0 = time.perf_counter()
        resp = await rag_service.process_query(
            query=query_text,
            retrieval_mode="multi_context",
            session_id=f"blind_{q_id}"
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)

        predicted_status = resp.evidence_status
        is_match = (predicted_status == expected_status)
        if is_match:
            correct_count += 1

        # Track FAR & FRR
        if expected_status == "SUFFICIENT":
            supported_total += 1
            if predicted_status != "SUFFICIENT":
                false_rejections += 1
        elif category == "single_clause" and expected_status in ["INSUFFICIENT", "PARTIAL"]:
            single_clause_unsupported_total += 1
            if predicted_status == "SUFFICIENT":
                single_clause_false_acceptances += 1
        elif expected_status in ["PARTIAL", "INSUFFICIENT"]:
            compound_nonsufficient_total += 1
            if predicted_status == "SUFFICIENT":
                compound_false_acceptances += 1

        symbol = "✓" if is_match else "✗"
        print(f"[{i:02d}/{len(questions)}] {q_id} ({category}): Expected={expected_status}, Predicted={predicted_status} {symbol} ({latency}ms)")

        results.append({
            "id": q_id,
            "query": query_text,
            "category": category,
            "expected_status": expected_status,
            "predicted_status": predicted_status,
            "match": is_match,
            "latency_ms": latency,
            "timing_breakdown": resp.timing_breakdown or {},
            "answer_preview": resp.answer[:200] + ("..." if len(resp.answer) > 200 else "")
        })

    total_queries = len(questions)
    accuracy = (correct_count / total_queries) * 100.0

    single_query_far = (single_clause_false_acceptances / single_clause_unsupported_total * 100.0) if single_clause_unsupported_total > 0 else 0.0
    compound_far = (compound_false_acceptances / compound_nonsufficient_total * 100.0) if compound_nonsufficient_total > 0 else 0.0
    frr = (false_rejections / supported_total * 100.0) if supported_total > 0 else 0.0

    print(f"\n=================================================")
    print(f"Phase 4.6 Blind Held-Out Benchmark Summary:")
    print(f"  Total Queries: {total_queries}")
    print(f"  Exact Matches: {correct_count}/{total_queries} ({accuracy:.2f}%)")
    print(f"  Single-Query FAR: {single_clause_false_acceptances}/{single_clause_unsupported_total} ({single_query_far:.2f}%)")
    print(f"  Compound/Non-Sufficient FAR: {compound_false_acceptances}/{compound_nonsufficient_total} ({compound_far:.2f}%)")
    print(f"  False Rejection Rate (FRR): {false_rejections}/{supported_total} ({frr:.2f}%)")
    print(f"=================================================\n")

    out_payload = {
        "metadata": {
            "title": "Phase 4.6 Blind Held-Out Benchmark Results",
            "total_queries": total_queries,
            "correct_queries": correct_count,
            "accuracy_percent": round(accuracy, 2),
            "single_query_far_percent": round(single_query_far, 2),
            "single_clause_false_acceptances": single_clause_false_acceptances,
            "single_clause_unsupported_total": single_clause_unsupported_total,
            "compound_far_percent": round(compound_far, 2),
            "compound_false_acceptances": compound_false_acceptances,
            "compound_nonsufficient_total": compound_nonsufficient_total,
            "frr_percent": round(frr, 2),
            "false_rejections": false_rejections,
            "supported_total": supported_total
        },
        "results": results
    }

    out_path = Path("evaluations/stage8_phase4_6/blind_test_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"Saved Deliverable 10 to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_blind_eval())
