"""Runner for Compound Query Decomposition and Grounding Evaluation."""

import asyncio
import json
import time
from pathlib import Path
from app.retrieval.evidence_coverage import evidence_coverage_evaluator
from app.services.rag_service import rag_service

async def main():
    dataset_path = Path("evaluations/stage8_phase4_4/compound_query_dataset.json")
    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    questions = data["questions"]
    results = []
    matches = 0

    print(f"Loaded {len(questions)} compound evaluation queries.\n")

    for idx, q in enumerate(questions, 1):
        t0 = time.perf_counter()
        report = await evidence_coverage_evaluator.evaluate_coverage(
            query=q["query"],
            retriever=rag_service.hybrid_retriever,
            query_analyzer=rag_service.query_analyzer,
            retrieval_mode="multi_context",
            top_k=4,
        )
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        
        is_match = (report.overall_evidence_status == q["expected_evidence_status"])
        if is_match:
            matches += 1
            mark = "PASS"
        else:
            mark = "FAIL"

        print(f"[{mark}] {q['id']} ({idx}/{len(questions)}): Expected={q['expected_evidence_status']}, Got={report.overall_evidence_status} ({latency_ms} ms)")
        if not is_match:
            print(f"   Query: {q['query']}")
            for sq in report.sub_questions:
                print(f"   - SubQ: {sq.text} -> Status: {sq.evidence_status} (Score: {sq.similarity_score:.4f}, Reason: {sq.decision_reason})")

        rec = {
            "id": q["id"],
            "query": q["query"],
            "category": q["category"],
            "expected_evidence_status": q["expected_evidence_status"],
            "actual_evidence_status": report.overall_evidence_status,
            "status_match": is_match,
            "is_compound": report.is_compound,
            "decomposition_type": report.decomposition_type,
            "coverage_ratio": report.coverage_ratio,
            "supported_count": report.supported_count,
            "unsupported_count": report.unsupported_count,
            "conflicting_count": report.conflicting_count,
            "decision_rationale": report.decision_rationale,
            "latency_ms": latency_ms,
            "sub_questions": [
                {
                    "id": sq.id,
                    "text": sq.text,
                    "aspect": sq.aspect,
                    "target_entity": sq.target_entity,
                    "evidence_status": sq.evidence_status,
                    "similarity_score": round(sq.similarity_score, 4),
                    "supporting_chunk_ids": sq.supporting_chunk_ids,
                    "missing_information": sq.missing_information,
                    "decision_reason": sq.decision_reason,
                }
                for sq in report.sub_questions
            ],
        }
        results.append(rec)

    accuracy = round(matches / len(questions) * 100, 2)
    print(f"\nCompleted: {matches}/{len(questions)} matched ({accuracy}% accuracy).")

    out_path = Path("evaluations/stage8_phase4_4/compound_query_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "metadata": {
                "phase": "Stage 8 Phase 4.4",
                "total_queries": len(questions),
                "matched_queries": matches,
                "accuracy_percent": accuracy,
            },
            "results": results,
        }, f, indent=2)
    print(f"Saved results to {out_path}")

if __name__ == "__main__":
    asyncio.run(main())
