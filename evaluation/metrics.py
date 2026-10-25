"""Evaluation metrics implementation for RAG pipeline benchmarking."""

from typing import List, Dict, Any


class RAGMetrics:
    """Calculates quantitative quality metrics for retrieved contexts and generated answers."""

    @staticmethod
    def compute_context_relevance(retrieved_texts: List[str], ground_truth_keywords: List[str]) -> float:
        """Measure what percentage of retrieved text contains ground truth concepts."""
        if not retrieved_texts or not ground_truth_keywords:
            return 0.0
        combined_text = " ".join(retrieved_texts).lower()
        matches = sum(1 for kw in ground_truth_keywords if kw.lower() in combined_text)
        return round(matches / len(ground_truth_keywords), 4)

    @staticmethod
    def compute_faithfulness(answer: str, context: str) -> float:
        """Measure token grounding between the synthesized answer and source contexts."""
        if not answer or not context:
            return 0.0
        answer_words = set(answer.lower().split())
        context_words = set(context.lower().split())
        grounded_words = answer_words.intersection(context_words)
        return round(len(grounded_words) / max(1, len(answer_words)), 4)

    @staticmethod
    def evaluate_sample(query: str, retrieved_contexts: List[str], answer: str, expected_keywords: List[str]) -> Dict[str, Any]:
        """Compute full metrics dictionary for a single evaluation case."""
        full_context = " ".join(retrieved_contexts)
        relevance = RAGMetrics.compute_context_relevance(retrieved_contexts, expected_keywords)
        faithfulness = RAGMetrics.compute_faithfulness(answer, full_context)

        return {
            "query": query,
            "context_relevance": relevance,
            "faithfulness": faithfulness,
            "overall_score": round((relevance * 0.5) + (faithfulness * 0.5), 4),
        }
