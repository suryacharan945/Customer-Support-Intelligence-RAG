"""Standalone Retrieval Evaluation CLI.

Runs the ground-truth benchmark queries against the active retriever and reports:
- Recall@1, Recall@3, Recall@5
- Mean Reciprocal Rank (MRR)
- Latency statistics (mean, p95)
- Per-query hit details
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.retrieval_evaluator import RetrievalEvaluator
from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.embeddings import get_embedding_provider
from app.core.config import settings
from app.core.logging import logger


def main():
    parser = argparse.ArgumentParser(description="Evaluate Semantic Retrieval Performance")
    parser.add_argument("--top-k", type=int, default=5, help="Top-K retrieval depth")
    parser.add_argument("--category-filter", action="store_true", help="Apply category filters during retrieval")
    parser.add_argument("--mock", action="store_true", help="Force mock embedding provider for testing")
    parser.add_argument("--export", action="store_true", help="Export summary to Google Drive 06_Test_Results")

    args = parser.parse_args()

    print("=" * 65)
    print("APEXPRINT RETRIEVAL EVALUATION BENCHMARK")
    print("=" * 65)

    provider = get_embedding_provider(
        provider_type="mock" if args.mock else settings.EMBEDDING_PROVIDER,
        allow_mock=args.mock,
    )
    print(f"Embedding Provider: {provider.__class__.__name__} ({provider.model_name})")
    print(f"Embedding Dimension: {provider.dimension}")
    print(f"Distance Metric:     {provider.distance_metric}")
    print(f"Top-K Parameter:     {args.top_k}")
    print(f"Category Filtering:  {args.category_filter}")
    print("-" * 65)

    retriever = VectorStoreRetriever(
        embedding_provider=provider,
        allow_mock=args.mock,
    )

    evaluator = RetrievalEvaluator()
    results = evaluator.evaluate_retriever(
        retriever=retriever,
        top_k=args.top_k,
        use_category_filter=args.category_filter,
    )

    agg = results["aggregate_metrics"]
    print(f"Total Benchmark Queries:     {results['total_queries']}")
    print(f"Supported Knowledge Queries: {results['supported_queries']}")
    print(f"Unsupported (Out-of-Domain): {results['unsupported_queries']}")
    print("-" * 65)
    print("AGGREGATE METRICS:")
    print(f"  Recall@1:          {agg['recall@1']:.4f}")
    print(f"  Recall@3:          {agg['recall@3']:.4f}")
    print(f"  Recall@5:          {agg['recall@5']:.4f}")
    print(f"  MRR:               {agg['mrr']:.4f}")
    print(f"  Mean Latency:      {agg['mean_latency_ms']:.2f} ms")
    print(f"  P95 Latency:       {agg['p95_latency_ms']:.2f} ms")
    print(f"  Latency Range:     {agg['min_latency_ms']:.2f} - {agg['max_latency_ms']:.2f} ms")
    print("=" * 65)

    if args.export:
        dest_dir = Path(settings.GOOGLE_DRIVE_ROOT) / "06_Test_Results"
        if dest_dir.exists():
            out_file = dest_dir / "retrieval_benchmark_results.json"
            out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(f"[EXPORT] Benchmark results saved to: {out_file}")


if __name__ == "__main__":
    main()
