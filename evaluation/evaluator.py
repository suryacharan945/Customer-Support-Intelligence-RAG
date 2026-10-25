"""RAG Evaluation runner with results export to persistent storage."""

import json
from pathlib import Path
from typing import List, Dict, Any
from evaluation.metrics import RAGMetrics
from app.core.config import settings
from app.core.logging import logger


class RAGEvaluator:
    """Runs automated benchmarking on test datasets."""

    def __init__(self, export_dir: str = None):
        self.export_dir = Path(export_dir or Path(settings.GOOGLE_DRIVE_ROOT) / "06_Test_Results")

    def run_benchmark(self, test_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute evaluation across multiple test samples."""
        results = []
        for sample in test_samples:
            eval_dict = RAGMetrics.evaluate_sample(
                query=sample["query"],
                retrieved_contexts=sample.get("contexts", []),
                answer=sample.get("answer", ""),
                expected_keywords=sample.get("expected_keywords", []),
            )
            results.append(eval_dict)

        avg_faithfulness = sum(r["faithfulness"] for r in results) / max(1, len(results))
        avg_relevance = sum(r["context_relevance"] for r in results) / max(1, len(results))

        summary = {
            "total_samples": len(results),
            "average_faithfulness": round(avg_faithfulness, 4),
            "average_context_relevance": round(avg_relevance, 4),
            "sample_results": results,
        }

        # Export if directory exists
        if self.export_dir.exists():
            out_file = self.export_dir / "latest_rag_benchmark_summary.json"
            try:
                out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
                logger.info(f"Evaluation benchmark exported to: {out_file}")
            except Exception as e:
                logger.warning(f"Could not export evaluation summary: {e}")

        return summary
