"""Hybrid Retrieval Combining Dense Semantic Embeddings and Sparse BM25 Keyword Matching."""

from typing import List, Dict
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.vector_store import VectorStoreRetriever
from app.core.config import settings


class HybridRetriever(BaseRetriever):
    """
    Fuses dense semantic retrieval scores with sparse keyword matches.
    """

    def __init__(self, vector_retriever: VectorStoreRetriever, alpha: float = 0.6):
        self.vector_retriever = vector_retriever
        self.alpha = alpha  # Weight for dense vs keyword (alpha * dense + (1 - alpha) * sparse)

    def _keyword_score(self, query: str, text: str) -> float:
        """Compute lightweight token overlap ratio as a deterministic BM25 proxy."""
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())
        if not query_tokens:
            return 0.0
        overlap = query_tokens.intersection(text_tokens)
        return len(overlap) / len(query_tokens)

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Perform hybrid retrieval with reciprocal score re-weighting."""
        dense_results = self.vector_retriever.retrieve(query, top_k=top_k * 2)
        fused_results: List[RetrievalResult] = []

        for item in dense_results:
            kw_score = self._keyword_score(query, item.text)
            hybrid_score = (self.alpha * item.score) + ((1.0 - self.alpha) * kw_score)
            fused_results.append(
                RetrievalResult(
                    document_id=item.document_id,
                    text=item.text,
                    score=hybrid_score,
                    source=item.source,
                    metadata=item.metadata,
                )
            )

        fused_results.sort(key=lambda x: x.score, reverse=True)
        return fused_results[:top_k]
