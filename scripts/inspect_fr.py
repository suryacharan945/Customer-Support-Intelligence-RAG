"""Inspect all non-SUFFICIENT classifications among supported queries."""

import json
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.rag_service import rag_service
from app.retrieval.evidence_gate import evidence_gate

P4_PATH = Path("evaluations/stage8_phase4_2/original_benchmark_results.json")
VAL_PATH = Path("evaluations/stage8_phase4_2/independent_validation_results.json")

async def inspect_non_sufficient_supported():
    p4_data = json.load(open(P4_PATH, encoding="utf-8"))
    val_data = json.load(open(VAL_PATH, encoding="utf-8"))
    
    # 1. P4 supported queries that were not SUFFICIENT:
    p4_non_suff = [
        r for r in p4_data["detailed_results"]
        if r["is_supported"] and r["actual_status"] != "SUFFICIENT"
    ]
    
    # 2. P4 queries where expected was PARTIAL:
    p4_exp_partial = [
        r for r in p4_data["detailed_results"]
        if r["is_supported"] and r["expected_status"] == "PARTIAL"
    ]
    
    # 3. Val supported queries that were not SUFFICIENT:
    val_non_suff = [
        r for r in val_data["detailed_results"]
        if r["is_supported"] and r["actual_status"] != "SUFFICIENT"
    ]
    
    print("="*70)
    print("P4 SUPPORTED QUERIES WITH ACTUAL != 'SUFFICIENT':")
    print("="*70)
    for r in p4_non_suff:
        print(f"\nID: {r['id']} | Exp: {r['expected_status']} | Act: {r['actual_status']}")
        print(f"Query: {r['query']}")
        
        # Test query retrieval and gate
        resp = await rag_service.process_query(r['query'], retrieval_mode="multi_context")
        print(f"Resp Evidence Status: {resp.evidence_status}")
        print(f"Preview: {resp.answer[:150].strip()}...")
        
        retriever = rag_service.hybrid_retriever
        analysis = rag_service.query_analyzer.analyze_query(r['query'])
        chunks = retriever.retrieve(r['query'], top_k=5, category=analysis.category_preferences, mode="hybrid", soft_category=analysis.soft_preference_only)
        gate_dec = evidence_gate.evaluate_evidence_sufficiency(r['query'], chunks)
        print(f"Top Dense: {gate_dec.top_similarity_score:.4f} | Gate Status: {gate_dec.status} | Reasons: {gate_dec.decision_reasons}")
        for idx, c in enumerate(chunks[:3], 1):
            print(f"  Chunk {idx}: {c.metadata.get('filename')} | Dense={c.metadata.get('dense_score')} | text={c.text[:80]}...")

    print("\n" + "="*70)
    print("INDEPENDENT SUPPORTED QUERIES WITH ACTUAL != 'SUFFICIENT':")
    print("="*70)
    for r in val_non_suff:
        print(f"\nID: {r['id']} | Exp: {r['expected_status']} | Act: {r['actual_status']}")
        print(f"Query: {r['query']}")
        resp = await rag_service.process_query(r['query'], retrieval_mode="multi_context")
        print(f"Resp Evidence Status: {resp.evidence_status}")
        retriever = rag_service.hybrid_retriever
        analysis = rag_service.query_analyzer.analyze_query(r['query'])
        chunks = retriever.retrieve(r['query'], top_k=5, category=analysis.category_preferences, mode="hybrid", soft_category=analysis.soft_preference_only)
        gate_dec = evidence_gate.evaluate_evidence_sufficiency(r['query'], chunks)
        print(f"Top Dense: {gate_dec.top_similarity_score:.4f} | Gate Status: {gate_dec.status} | Reasons: {gate_dec.decision_reasons}")
        for idx, c in enumerate(chunks[:3], 1):
            print(f"  Chunk {idx}: {c.metadata.get('filename')} | Dense={c.metadata.get('dense_score')} | text={c.text[:80]}...")

    print("\n" + "="*70)
    print("P4 CATEGORY G (AMBIGUOUS / PARTIAL) QUERIES (5 total):")
    print("="*70)
    for r in p4_exp_partial:
        print(f"\nID: {r['id']} | Exp: {r['expected_status']} | Act: {r['actual_status']}")
        print(f"Query: {r['query']}")
        print(f"Preview: {r['answer_preview'][:150]}...")

if __name__ == "__main__":
    asyncio.run(inspect_non_sufficient_supported())
