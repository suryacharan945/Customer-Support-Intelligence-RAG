"""Test query token containment across all benchmark queries."""

import json
import re
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.retrieval.evidence_gate import evidence_gate
from app.services.rag_service import rag_service

P4_PATH = Path("evaluations/stage8_phase4_2/original_benchmark_results.json")
VAL_PATH = Path("evaluations/stage8_phase4_2/independent_validation_results.json")

async def test_containment():
    p4_data = json.load(open(P4_PATH, encoding="utf-8"))["detailed_results"]
    val_data = json.load(open(VAL_PATH, encoding="utf-8"))["detailed_results"]
    
    all_queries = p4_data + val_data
    
    stop_words = evidence_gate.GENERIC_STOP_WORDS | {
        "what", "how", "why", "when", "where", "which", "does", "doesnt", "explain",
        "describe", "compare", "between", "difference", "versus", "across", "about",
        "please", "tell", "give", "show", "used", "using", "standard", "system",
        "printer", "printers", "platform", "model", "units", "apexprint", "prox-400",
        "colorwave-850", "ecotank", "l3150"
    }
    
    print(f"Testing {len(all_queries)} queries...")
    for q_item in all_queries:
        qid = q_item["id"]
        q_text = q_item["query"]
        exp = q_item["expected_status"]
        is_supp = q_item["is_supported"]
        
        # Extract informative content words
        words = [w for w in re.findall(r"\b[a-zA-Z]{4,}\b", q_text.lower()) if w not in stop_words]
        if not words:
            continue
            
        # Get retrieved contexts for this query
        analysis = rag_service.query_analyzer.analyze_query(q_text)
        retriever = rag_service.hybrid_retriever
        chunks = retriever.retrieve(q_text, top_k=5, category=analysis.category_preferences, mode="hybrid", soft_category=analysis.soft_preference_only)
        combined_text = " ".join(c.text.lower() for c in chunks)
        
        matched_words = [w for w in words if w in combined_text]
        ratio = len(matched_words) / len(words)
        
        # Only print interesting cases: where ratio is low or unsupported
        if not is_supp or ratio < 0.40 or exp in ["PARTIAL", "INSUFFICIENT"]:
            print(f"[{qid}] Supp={is_supp} Exp={exp} | Ratio={ratio:.2f} ({len(matched_words)}/{len(words)})")
            print(f"  Query: {q_text}")
            print(f"  Missing: {[w for w in words if w not in combined_text]}")
            print(f"  Matched: {matched_words}")
            print()

if __name__ == "__main__":
    asyncio.run(test_containment())
