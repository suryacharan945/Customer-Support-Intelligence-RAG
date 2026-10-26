"""BM25Okapi Keyword Search Engine for Exact Term & Identifier Matching.

Implements standard Okapi BM25 ranking algorithm with:
- Alphanumeric tokenization preserving hardware error codes (E-101, E-204) and model numbers (ProX-400).
- Standard Robertson-Spärck Jones IDF with smoothing.
- Length normalization with standard constants k1=1.5 and b=0.75.
- Fast numpy/python vector scoring.
"""

import math
import re
from typing import List, Dict, Any, Optional, Set
from app.ingestion.chunker import TextChunk
from app.retrieval.base import BaseRetriever, RetrievalResult


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric terms, preserving hyphenated codes."""
    return [t.lower() for t in re.findall(r"\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b", text)]


class BM25Retriever(BaseRetriever):
    """
    BM25Okapi sparse keyword retriever operating over TextChunk collections.
    """

    def __init__(
        self,
        chunks: Optional[List[TextChunk]] = None,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.k1 = k1
        self.b = b
        self.chunks: List[TextChunk] = []
        self.doc_len: List[int] = []
        self.avg_doc_len: float = 0.0
        self.corpus_size: int = 0
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.term_freqs: List[Dict[str, int]] = []

        if chunks:
            self.index_chunks(chunks)

    def index_chunks(self, chunks: List[TextChunk]) -> int:
        """Build BM25 inverted index from provided text chunks."""
        self.chunks = list(chunks)
        self.corpus_size = len(self.chunks)
        self.doc_len = []
        self.doc_freqs = {}
        self.term_freqs = []

        total_len = 0
        for chunk in self.chunks:
            tokens = tokenize(chunk.text)
            length = len(tokens)
            self.doc_len.append(length)
            total_len += length

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for t in set(tokens):
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = total_len / max(1, self.corpus_size)

        # Compute Robertson-Spärck Jones IDF
        self.idf = {}
        for term, df in self.doc_freqs.items():
            # Standard smoothed BM25 IDF: ln((N - df + 0.5) / (df + 0.5) + 1)
            self.idf[term] = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

        return self.corpus_size

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str | List[str]] = None,
    ) -> List[RetrievalResult]:
        """
        Rank indexed chunks using BM25Okapi scoring with optional category filtering.
        """
        if self.corpus_size == 0 or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        allowed_cats: Optional[Set[str]] = None
        if category:
            if isinstance(category, str):
                allowed_cats = {category}
            else:
                allowed_cats = set(category)

        scores: List[float] = [0.0] * self.corpus_size

        for term in query_tokens:
            if term not in self.idf:
                continue
            term_idf = self.idf[term]

            for i in range(self.corpus_size):
                tf = self.term_freqs[i].get(term, 0)
                if tf == 0:
                    continue

                d_len = self.doc_len[i]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len))
                scores[i] += term_idf * (tf * (self.k1 + 1.0)) / denom

        # Sort indices by descending score
        ranked_indices = sorted(range(self.corpus_size), key=lambda idx: scores[idx], reverse=True)

        results: List[RetrievalResult] = []
        max_score = max(scores) if scores and max(scores) > 0 else 1.0

        for idx in ranked_indices:
            score = scores[idx]
            if score <= 0.0:
                continue

            chunk = self.chunks[idx]
            if allowed_cats and chunk.category not in allowed_cats:
                continue

            normalized_score = min(1.0, score / max_score)
            results.append(
                RetrievalResult(
                    document_id=chunk.document_id,
                    text=chunk.text,
                    score=round(normalized_score, 4),
                    source=chunk.source,
                    metadata={
                        "document_id": chunk.document_id,
                        "chunk_id": chunk.chunk_id,
                        "category": chunk.category,
                        "page_number": chunk.page_number,
                        "content_hash": chunk.content_hash,
                        "bm25_raw_score": round(score, 4),
                        "retrieval_method": "bm25",
                    },
                )
            )
            if len(results) >= top_k:
                break

        return results
