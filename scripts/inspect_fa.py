"""Extract and inspect the 4 false acceptances in the independent validation benchmark."""

import json
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.rag_service import rag_service
from app.retrieval.evidence_gate import evidence_gate

VAL_PATH = Path("evaluations/stage8_phase4_2/independent_validation_results.json")
VAL_DATASET_PATH = Path("evaluations/stage8_phase4_2/independent_validation_dataset.json")

async def inspect_false_acceptances():
    val_data = json.load(open(VAL_PATH, encoding="utf-8"))
    val_dataset = json.load(open(VAL_DATASET_PATH, encoding="utf-8"))
    dataset_by_id = {q["id"]: q for q in val_dataset["questions"]}
    
    # False acceptances: is_supported == False and actual_status == "SUFFICIENT"
    fa_records = [
        r for r in val_data["detailed_results"]
        if not r["is_supported"] and r["actual_status"] == "SUFFICIENT"
    ]
    
    print(f"Total False Acceptances: {len(fa_records)}")
    
    for r in fa_records:
        qid = r["id"]
        q_item = dataset_by_id.get(qid, {})
        query = r["query"]
        print("\n" + "="*70)
        print(f"Query ID: {qid}")
        print(f"Query: {query}")
        print(f"Expected Status: {r['expected_status']}")
        print(f"Actual Status: {r['actual_status']}")
        print(f"Taxonomy Category: {r.get('category')}")
        print(f"Dataset Rationale: {q_item.get('labeling_rationale')}")
        
        # Now re-run process_query with live diagnostics to capture all scores and pipeline decisions
        resp = await rag_service.process_query(query, retrieval_mode="multi_context")
        
        print("\n--- Pipeline Execution Diagnostics ---")
        print(f"Selected Categories: {resp.selected_categories}")
        print(f"Retrieval Mode: {resp.retrieval_mode}")
        print(f"Evidence Status: {resp.evidence_status}")
        print(f"Provider Status: {resp.provider_status}")
        
        # We can also call the hybrid retriever directly to get candidate chunks and their scores
        retriever = rag_service.hybrid_retriever
        analysis = rag_service.query_analyzer.analyze_query(query)
        selected_cats = analysis.category_preferences
        ret_results = retriever.retrieve(
            query=query,
            top_k=5,
            category=selected_cats,
            mode="hybrid",
            soft_category=analysis.soft_preference_only
        )
        
        print(f"\nRetrieved {len(ret_results)} Chunks:")
        for idx, chunk in enumerate(ret_results, 1):
            cid = chunk.metadata.get("chunk_id") or chunk.document_id
            fn = chunk.metadata.get("filename") or chunk.source
            cat = chunk.metadata.get("category")
            dense_s = chunk.metadata.get("dense_score")
            sparse_s = chunk.metadata.get("sparse_score")
            rrf_s = chunk.score
            print(f"  [{idx}] Doc: {fn} | Chunk: {cid} | Cat: {cat}")
            print(f"      Dense Score: {dense_s} | Sparse (BM25): {sparse_s} | RRF Score: {rrf_s:.6f}")
            print(f"      Snippet: {chunk.text[:120].strip()}...")
            
        gate_decision = evidence_gate.evaluate_evidence_sufficiency(query, ret_results)
        print("\n--- Evidence Gate Decisions ---")
        print(f"Gate Status: {gate_decision.status}")
        print(f"Similarity Floor Passed: {gate_decision.similarity_floor_passed} (Top Dense: {gate_decision.top_similarity_score})")
        print(f"Entity Result: {gate_decision.entity_result}")
        print(f"Policy Result: {gate_decision.policy_result}")
        print(f"Gate Decision Reasons: {gate_decision.decision_reasons}")
        
        print("\n--- Generated Answer & Grounding Check ---")
        print(f"Answer:\n{resp.answer}")
        print(f"Supporting Citations Count: {len(resp.supporting_citations)}")
        for sc in resp.supporting_citations:
            print(f"  - Cited: {sc.document_source} ({sc.page_or_section}) Verified={sc.is_verified}")

if __name__ == "__main__":
    asyncio.run(inspect_false_acceptances())
