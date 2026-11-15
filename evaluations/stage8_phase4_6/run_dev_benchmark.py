#!/usr/bin/env python3
"""
Evaluate the Stage 8 Phase 4.6 Development Benchmark (20 questions).
Outputs evaluations/stage8_phase4_6/development_results.json (Deliverable 8).
"""

import sys
import json
import time
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.services.rag_service import rag_service

async def run_dev_eval():
    dev_path = Path("evaluations/stage8_phase4_6/development_dataset.json")
    with open(dev_path, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    questions = dev_data["questions"]
    print(f"--- Running Phase 4.6 Development Benchmark ({len(questions)} queries) ---")

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
            session_id=f"dev_{q_id}"
        )
        latency = round((time.perf_counter() - t0) * 1000, 2)

        predicted_status = resp.evidence_status
        is_match = (predicted_status == expected_status)
        if is_match:
            correct_count += 1

        symbol = "✓" if is_match else "✗"
        print(f"[{i:02d}/20] {q_id}: Expected={expected_status}, Predicted={predicted_status} {symbol} ({latency}ms)")

        results.append({
            "id": q_id,
            "query": query_text,
            "category": q.get("category"),
            "expected_status": expected_status,
            "predicted_status": predicted_status,
            "match": is_match,
            "latency_ms": latency,
            "answer_preview": resp.answer[:200] + ("..." if len(resp.answer) > 200 else "")
        })

    accuracy = (correct_count / len(questions)) * 100.0
    print(f"\nDevelopment Benchmark Complete: {correct_count}/{len(questions)} ({accuracy:.2f}% Accuracy)")

    out_payload = {
        "metadata": {
            "title": "Phase 4.6 Development Benchmark Results",
            "total_queries": len(questions),
            "correct_queries": correct_count,
            "accuracy_percent": round(accuracy, 2)
        },
        "results": results
    }

    out_path = Path("evaluations/stage8_phase4_6/development_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_payload, f, indent=2)
    print(f"Saved Deliverable 8 to {out_path}")

if __name__ == "__main__":
    asyncio.run(run_dev_eval())
