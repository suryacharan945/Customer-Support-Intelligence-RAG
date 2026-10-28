"""Hybrid Retrieval Engine Combining Dense Semantic Embeddings and Sparse BM25 Keyword Search.

Implements Reciprocal Rank Fusion (RRF) with configurable dense/sparse weighting,
strict chunk deduplication, category filtering, and metadata preservation.
"""

import time
from typing import List, Dict, Any, Optional, Set, Tuple
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.bm25 import BM25Retriever
from app.core.config import settings
from app.core.logging import logger


class HybridRetriever(BaseRetriever):
    """
    Fuses dense semantic retrieval with sparse BM25 keyword retrieval using Reciprocal Rank Fusion (RRF).
    Supports category filtering, deduplication by chunk ID, and dense-only baseline mode.
    """

    def __init__(
        self,
        vector_retriever: BaseRetriever,
        bm25_retriever: Optional[BM25Retriever] = None,
        alpha: float = settings.HYBRID_SEARCH_ALPHA,
        rrf_k: int = 60,
    ):
        """
        Args:
            vector_retriever: Dense retriever (VectorStoreRetriever or RealExactSemanticRetriever).
            bm25_retriever: Sparse BM25 retriever (optional; if None, falls back to dense-only or proxy).
            alpha: Dense weight in [0.0, 1.0]. Sparse weight is (1.0 - alpha).
            rrf_k: Reciprocal Rank Fusion constant (standard TREC default = 60).
        """
        self.vector_retriever = vector_retriever
        self.bm25_retriever = bm25_retriever
        self.alpha = alpha
        self.rrf_k = rrf_k

    def _keyword_score(self, query: str, text: str) -> float:
        """Lightweight token overlap ratio proxy when BM25 index is not provided."""
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())
        if not query_tokens:
            return 0.0
        overlap = query_tokens.intersection(text_tokens)
        return len(overlap) / len(query_tokens)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str | List[str]] = None,
        mode: str = "hybrid",
    ) -> List[RetrievalResult]:
        """
        Execute retrieval across dense and/or sparse channels and fuse results.
        """
        results, timings = self.retrieve_with_timings(query, top_k=top_k, category=category, mode=mode)
        self.last_timings = timings
        return results

    def retrieve_with_timings(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str | List[str]] = None,
        mode: str = "hybrid",
    ) -> Tuple[List[RetrievalResult], Dict[str, float]]:
        """
        Execute retrieval across dense and/or sparse channels and fuse results,
        returning both the ranked results and granular sub-millisecond stage timings.

        Args:
            query: User search string.
            top_k: Maximum number of merged results to return.
            category: Optional category filter string or list of category strings.
            mode: 'hybrid' (RRF fusion), 'dense' (dense-only baseline), or 'bm25' (keyword-only).

        Returns:
            Tuple of (ranked_results, timings_dict).
        """
        t0_total = time.perf_counter()
        timings: Dict[str, float] = {
            "dense_ms": 0.0,
            "sparse_ms": 0.0,
            "fusion_ms": 0.0,
            "total_retrieval_ms": 0.0,
        }

        if not query or not query.strip():
            timings["total_retrieval_ms"] = round((time.perf_counter() - t0_total) * 1000, 3)
            return [], timings

        # 1. Dense Retrieval
        dense_results: List[RetrievalResult] = []
        if mode in ("hybrid", "dense"):
            t0_dense = time.perf_counter()
            fetch_k = top_k * 3 if mode == "hybrid" else top_k
            # If category is a list of categories, query per-category or unconstrained
            if isinstance(category, list) and len(category) == 1:
                cat_arg = category[0]
            elif isinstance(category, str):
                cat_arg = category
            else:
                cat_arg = None  # Filter after retrieval if list of multiple categories

            try:
                # Handle base retrievers with or without category parameter
                dense_results = self.vector_retriever.retrieve(
                    query, top_k=fetch_k, category=cat_arg
                )
            except TypeError:
                dense_results = self.vector_retriever.retrieve(query, top_k=fetch_k)

            # In-memory post-filter if category was a multi-item list
            if isinstance(category, list) and len(category) > 1:
                allowed_set = set(category)
                dense_results = [
                    r for r in dense_results if r.metadata.get("category") in allowed_set
                ]
            timings["dense_ms"] = round((time.perf_counter() - t0_dense) * 1000, 3)

        if mode == "dense":
            timings["total_retrieval_ms"] = round((time.perf_counter() - t0_total) * 1000, 3)
            return dense_results[:top_k], timings

        # 2. Sparse BM25 Retrieval
        sparse_results: List[RetrievalResult] = []
        if mode in ("hybrid", "bm25") and self.bm25_retriever:
            t0_sparse = time.perf_counter()
            fetch_k = top_k * 3 if mode == "hybrid" else top_k
            sparse_results = self.bm25_retriever.retrieve(
                query, top_k=fetch_k, category=category
            )
            timings["sparse_ms"] = round((time.perf_counter() - t0_sparse) * 1000, 3)

        if mode == "bm25":
            timings["total_retrieval_ms"] = round((time.perf_counter() - t0_total) * 1000, 3)
            return sparse_results[:top_k], timings

        # 3. Fallback to token overlap if BM25 index is not populated
        t0_fusion = time.perf_counter()
        if not sparse_results and dense_results:
            # Fallback to linear proxy score re-weighting
            fused_results: List[RetrievalResult] = []
            for item in dense_results:
                kw_score = self._keyword_score(query, item.text)
                hybrid_score = (self.alpha * item.score) + ((1.0 - self.alpha) * kw_score)
                meta = {**item.metadata, "hybrid_score": round(hybrid_score, 4)}
                fused_results.append(
                    RetrievalResult(
                        document_id=item.document_id,
                        text=item.text,
                        score=round(hybrid_score, 4),
                        source=item.source,
                        metadata=meta,
                    )
                )
            fused_results.sort(key=lambda x: x.score, reverse=True)
            timings["fusion_ms"] = round((time.perf_counter() - t0_fusion) * 1000, 3)
            timings["total_retrieval_ms"] = round((time.perf_counter() - t0_total) * 1000, 3)
            return fused_results[:top_k], timings

        # 4. Reciprocal Rank Fusion (RRF)
        # Key: chunk_id (or document_id) -> merged item
        rrf_scores: Dict[str, float] = {}
        items_by_id: Dict[str, RetrievalResult] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}

        w_dense = self.alpha
        w_sparse = 1.0 - self.alpha

        for rank, res in enumerate(dense_results, start=1):
            cid = res.metadata.get("chunk_id") or res.document_id
            dense_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (w_dense / (self.rrf_k + rank))
            if cid not in items_by_id:
                items_by_id[cid] = res

        for rank, res in enumerate(sparse_results, start=1):
            cid = res.metadata.get("chunk_id") or res.document_id
            sparse_ranks[cid] = rank
            rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (w_sparse / (self.rrf_k + rank))
            if cid not in items_by_id:
                items_by_id[cid] = res

        # Sort all deduplicated chunks by descending RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        final_results: List[RetrievalResult] = []
        max_rrf = max(rrf_scores.values()) if rrf_scores else 1.0

        for cid in sorted_ids[:top_k]:
            orig = items_by_id[cid]
            meta = {
                **orig.metadata,
                "rrf_score": round(rrf_scores[cid], 5),
                "dense_rank": dense_ranks.get(cid, None),
                "sparse_rank": sparse_ranks.get(cid, None),
                "retrieval_method": "hybrid_rrf",
            }
            # Normalize RRF score to [0, 1] relative to max achievable score in this query
            normalized_score = min(1.0, rrf_scores[cid] / max_rrf)
            final_results.append(
                RetrievalResult(
                    document_id=orig.document_id,
                    text=orig.text,
                    score=round(normalized_score, 4),
                    source=orig.source,
                    metadata=meta,
                )
            )

        timings["fusion_ms"] = round((time.perf_counter() - t0_fusion) * 1000, 3)
        timings["total_retrieval_ms"] = round((time.perf_counter() - t0_total) * 1000, 3)
        return final_results, timings
