#!/usr/bin/env python3
"""
Evaluate the Phase 4.5 Blind Challenge Benchmark (30 questions) with Phase 4.6 Engine.
Compares Phase 4.5 (40% accuracy, 61.9% FAR) against Phase 4.6 Universal Grounding.
"""

import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service

async def run_p4_5_blind_eval():
    p4_5_blind_path = Path("evaluations/stage8_phase4_5/blind_compound_query_dataset.json")
    with open(p4_5_blind_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    print(f"--- Running Phase 4.5 Blind Challenge Queries ({len(questions)} queries) on Phase 4.6 Engine ---")

    results = []
    correct_count = 0
    unsupported_total = 0
    false_acceptances = 0

    for i, q in enumerate(questions, 1):
        q_id = q["id"]
        query_text = q["query"]
        expected_status = q["expected_evidence_status"]

        t0 = time.perf_counter()
        resp = await rag_service.process_query(
            query=query_text,
            retrieval_mode="multi_context",
            session_id=f"p45_blind_{q_id}"
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)

        predicted_status = resp.evidence_status
        is_match = (predicted_status == expected_status)
        if is_match:
            correct_count += 1

        if expected_status in ["PARTIAL", "INSUFFICIENT"]:
            unsupported_total += 1
            if predicted_status == "SUFFICIENT":
                false_acceptances += 1

        symbol = "✓" if is_match else "✗"
        print(f"[{i:02d}/30] {q_id}: Expected={expected_status}, Predicted={predicted_status} {symbol} ({latency}ms)")

        results.append({
            "id": q_id,
            "query": query_text,
            "expected_status": expected_status,
            "predicted_status": predicted_status,
            "match": is_match,
            "latency_ms": latency
        })

    accuracy = (correct_count / len(questions)) * 100.0
    far = (false_acceptances / unsupported_total * 100.0) if unsupported_total > 0 else 0.0

    print(f"\nPhase 4.5 Blind Evaluation on Phase 4.6 Engine:")
    print(f"  Exact Matches: {correct_count}/{len(questions)} ({accuracy:.2f}%) [was 12/30 (40.0%)]")
    print(f"  False Acceptance Rate: {false_acceptances}/{unsupported_total} ({far:.2f}%) [was 13/21 (61.9%)]")

    out_payload = {
        "metadata": {
            "title": "Phase 4.5 Blind Queries Re-evaluated on Phase 4.6 Engine",
            "total_queries": len(questions),
            "correct_queries": correct_count,
            "accuracy_percent": round(accuracy, 2),
            "phase4_5_baseline_accuracy_percent": 40.0,
            "false_acceptances": false_acceptances,
            "unsupported_total": unsupported_total,
            "far_percent": round(far, 2),
            "phase4_5_baseline_far_percent": 61.9
        },
        "results": results
    }

    out_path = Path("evaluations/stage8_phase4_6/phase4_5_blind_reevaluation.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"Saved to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_p4_5_blind_eval())
