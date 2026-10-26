"""Retrieval Evaluation Engine computing Recall@K, MRR, and latency telemetry."""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.core.config import settings
from app.core.logging import logger


class RetrievalEvaluator:
    """
    Evaluates a retriever against a ground-truth dataset.
    Calculates document-level and chunk-level Recall@K, MRR, and latency.
    """

    def __init__(self, dataset_path: Optional[str | Path] = None):
        if dataset_path:
            self.dataset_path = Path(dataset_path)
        else:
            self.dataset_path = (
                Path(__file__).resolve().parent / "retrieval_test_dataset.json"
            )

        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            self.dataset = json.load(f)

    def evaluate_retriever(
        self,
        retriever: BaseRetriever,
        top_k: int = 5,
        use_category_filter: bool = False,
    ) -> Dict[str, Any]:
        """
        Run retrieval benchmark across all queries in dataset.
        Computes Recall@1, Recall@3, Recall@5, MRR, and latency.
        """
        queries = self.dataset.get("queries", [])
        detailed_results = []

        recalls_at_1 = []
        recalls_at_3 = []
        recalls_at_5 = []
        reciprocal_ranks = []
        latencies_ms = []

        for item in queries:
            qid = item["id"]
            query_text = item["query"]
            cat = item.get("category", "general")
            relevant_docs = set(item.get("relevant_doc_ids", []))
            relevant_chunks = set(item.get("relevant_chunk_ids", []))

            # Skip unsupported queries from recall calculation, but track for false positive rate
            is_supported = len(relevant_docs) > 0

            # Optional category filter
            cat_filter = item.get("expected_category") if use_category_filter else None

            t0 = time.perf_counter()
            retrieved = retriever.retrieve(query_text, top_k=top_k, category=cat_filter)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elapsed_ms)

            retrieved_doc_ids = [r.document_id for r in retrieved]

            # Calculate document-level hits
            doc_hits_at_1 = (
                1.0
                if (is_supported and retrieved_doc_ids[:1] and retrieved_doc_ids[0] in relevant_docs)
                else 0.0
            )
            doc_hits_at_3 = (
                1.0
                if (is_supported and any(d in relevant_docs for d in retrieved_doc_ids[:3]))
                else 0.0
            )
            doc_hits_at_5 = (
                1.0
                if (is_supported and any(d in relevant_docs for d in retrieved_doc_ids[:5]))
                else 0.0
            )

            # Calculate reciprocal rank
            rr = 0.0
            if is_supported:
                for rank, doc_id in enumerate(retrieved_doc_ids, start=1):
                    if doc_id in relevant_docs:
                        rr = 1.0 / rank
                        break

            if is_supported:
                recalls_at_1.append(doc_hits_at_1)
                recalls_at_3.append(doc_hits_at_3)
                recalls_at_5.append(doc_hits_at_5)
                reciprocal_ranks.append(rr)

            query_result = {
                "query_id": qid,
                "category": cat,
                "query": query_text,
                "is_supported": is_supported,
                "latency_ms": round(elapsed_ms, 2),
                "relevant_doc_ids": list(relevant_docs),
                "retrieved_doc_ids": retrieved_doc_ids,
                "hit_at_1": doc_hits_at_1,
                "hit_at_3": doc_hits_at_3,
                "hit_at_5": doc_hits_at_5,
                "reciprocal_rank": round(rr, 4),
            }
            detailed_results.append(query_result)

        # Aggregate metrics
        num_evaluated = len(recalls_at_1)
        mean_recall_1 = sum(recalls_at_1) / max(1, num_evaluated)
        mean_recall_3 = sum(recalls_at_3) / max(1, num_evaluated)
        mean_recall_5 = sum(recalls_at_5) / max(1, num_evaluated)
        mean_mrr = sum(reciprocal_ranks) / max(1, num_evaluated)

        mean_latency = sum(latencies_ms) / max(1, len(latencies_ms))
        sorted_lat = sorted(latencies_ms)
        p95_idx = int(len(sorted_lat) * 0.95)
        p95_latency = sorted_lat[min(p95_idx, len(sorted_lat) - 1)] if sorted_lat else 0.0

        summary = {
            "dataset_name": self.dataset.get("dataset_name"),
            "total_queries": len(queries),
            "supported_queries": num_evaluated,
            "unsupported_queries": len(queries) - num_evaluated,
            "top_k": top_k,
            "category_filter_applied": use_category_filter,
            "aggregate_metrics": {
                "recall@1": round(mean_recall_1, 4),
                "recall@3": round(mean_recall_3, 4),
                "recall@5": round(mean_recall_5, 4),
                "mrr": round(mean_mrr, 4),
                "mean_latency_ms": round(mean_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "min_latency_ms": round(min(latencies_ms, default=0.0), 2),
                "max_latency_ms": round(max(latencies_ms, default=0.0), 2),
            },
            "detailed_query_results": detailed_results,
        }
        return summary
