#!/usr/bin/env python3
"""
Evaluate the Stage 8 Phase 4.6 Validation Benchmark (25 questions).
Outputs evaluations/stage8_phase4_6/validation_results.json (Deliverable 9).
"""

import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service

async def run_val_eval():
    val_path = Path("evaluations/stage8_phase4_6/validation_dataset.json")
    with open(val_path, "r", encoding="utf-8") as f:
        val_data = json.load(f)

    questions = val_data["questions"]
    print(f"--- Running Phase 4.6 Validation Benchmark ({len(questions)} queries) ---")

    results = []
    correct_count = 0

    for i, q in enumerate(questions, 1):
        q_id = q["id"]
        query_text = q["query"]
        expected_status = q["expected_status"]

        t0 = time.perf_counter()
        resp = await rag_service.process_query(
            query=query_text,
            retrieval_mode="multi_context",
            session_id=f"val_{q_id}"
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)

        predicted_status = resp.evidence_status
        is_match = (predicted_status == expected_status)
        if is_match:
            correct_count += 1

        symbol = "✓" if is_match else "✗"
        print(f"[{i:02d}/{len(questions)}] {q_id}: Expected={expected_status}, Predicted={predicted_status} {symbol} ({latency}ms)")

        results.append({
            "id": q_id,
            "query": query_text,
            "expected_status": expected_status,
            "predicted_status": predicted_status,
            "match": is_match,
            "latency_ms": latency,
            "timing_breakdown": resp.timing_breakdown or {},
            "answer_preview": resp.answer[:200] + ("..." if len(resp.answer) > 200 else "")
        })

    accuracy = (correct_count / len(questions)) * 100.0
    print(f"\nValidation Benchmark Complete: {correct_count}/{len(questions)} ({accuracy:.2f}% Accuracy)")

    out_payload = {
        "metadata": {
            "title": "Phase 4.6 Validation Benchmark Results",
            "total_queries": len(questions),
            "correct_queries": correct_count,
            "accuracy_percent": round(accuracy, 2)
        },
        "results": results
    }

    out_path = Path("evaluations/stage8_phase4_6/validation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"Saved Deliverable 9 to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_val_eval())
