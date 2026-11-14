import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
from app.retrieval.vector_store import VectorStoreRetriever

retriever = VectorStoreRetriever()

with open("evaluations/stage8_phase4/dataset/benchmark_50_questions.json") as f:
    data = json.load(f)
questions = data["questions"] if isinstance(data, dict) and "questions" in data else data

results = []
for q in questions:
    qid = q["id"]
    query = q["query"]
    taxonomy = q.get("type") or q.get("taxonomy") or "General"
    is_supported = (q.get("expected_status") != "INSUFFICIENT" and "Type H" not in str(taxonomy))
    res = retriever.retrieve(query, top_k=5)
    top1_score = res[0].score if res else 0.0
    top3_mean_score = sum(r.score for r in res[:3]) / max(1, len(res[:3])) if res else 0.0
    top5_mean_score = sum(r.score for r in res) / max(1, len(res)) if res else 0.0
    top1_doc = res[0].source if res else ""
    results.append({
        "id": qid,
        "is_supported": is_supported,
        "taxonomy": taxonomy,
        "query": query,
        "top1_score": round(top1_score, 4),
        "top3_mean": round(top3_mean_score, 4),
        "top5_mean": round(top5_mean_score, 4),
        "top1_doc": top1_doc,
    })

print(f"{'ID':<8} | {'Supp':<5} | {'Top1':<7} | {'Top3':<7} | {'Top5':<7} | {'Taxonomy':<35} | {'Top1 Doc'}")
print("-" * 110)
for r in results:
    s_str = "YES" if r["is_supported"] else "NO"
    tax = r["taxonomy"] or "Unknown"
    print(f"{r['id']:<8} | {s_str:<5} | {r['top1_score']:<7.4f} | {r['top3_mean']:<7.4f} | {r['top5_mean']:<7.4f} | {tax[:35]:<35} | {r['top1_doc'][:30]}")

with open("evaluations/stage8_phase4_1/calibration_scores.json", "w") as f:
    json.dump(results, f, indent=2)
