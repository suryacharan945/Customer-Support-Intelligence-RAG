import json
import time
from app.services.rag_service import RAGService
from app.retrieval.query_analyzer import query_analyzer

rag = RAGService()

queries = [
    "Explain the overall project architecture.",
    "What technologies are used in the frontend?",
    "Explain the backend architecture.",
    "What is Multi-Context Prompting?",
    "Explain the hybrid retrieval pipeline.",
    "What are the benchmark results?",
    "Explain the storage constraints.",
]

results = []
for q in queries:
    analysis = query_analyzer.analyze_query(q)
    t0 = time.perf_counter()
    retrieved = rag.hybrid_retriever.retrieve(
        query=q,
        top_k=5,
        category=None,
        mode="hybrid",
        soft_category=True,
    )
    lat_ms = round((time.perf_counter() - t0) * 1000, 2)
    
    dossier_chunks = [
        r for r in retrieved 
        if "dossier" in (r.source or "").lower() or "dossier" in (r.metadata.get("filename") or "").lower()
    ]
    
    top_items = []
    for r in retrieved[:3]:
        top_items.append({
            "chunk_id": r.metadata.get("chunk_id"),
            "source": r.source or r.metadata.get("filename"),
            "page": r.metadata.get("page_number"),
            "category": r.metadata.get("category"),
            "score": r.score,
            "snippet": r.text[:120].strip() + "..."
        })
    
    results.append({
        "query": q,
        "intent": analysis.primary_intent,
        "is_customer_support": analysis.is_customer_support,
        "retrieved_count": len(retrieved),
        "dossier_chunks_retrieved": len(dossier_chunks),
        "retrieval_latency_ms": lat_ms,
        "top_matches": top_items
    })

output_path = "evaluation/stage8_baseline/phase1_dossier_retrieval_evaluation.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"Evaluation complete for {len(results)} queries.")
for res in results:
    q_text = res["query"]
    intent = res["intent"]
    hits = res["dossier_chunks_retrieved"]
    lat = res["retrieval_latency_ms"]
    print(f"Query: {q_text}")
    print(f"  Intent: {intent} | Dossier hits: {hits}/5 | Latency: {lat}ms")
    if res["top_matches"]:
        top = res["top_matches"][0]
        cid = top["chunk_id"]
        page = top["page"]
        snip = top["snippet"]
        print(f"  Top match: [{cid}] (Page {page}) {snip[:80]}...")
