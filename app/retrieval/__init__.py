"""Retrieval subsystem initialization."""

from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.retrieval.category_selector import CategorySelector, category_selector, CategorySelectionResult

__all__ = [
    "BaseRetriever",
    "RetrievalResult",
    "VectorStoreRetriever",
    "BM25Retriever",
    "HybridRetriever",
    "CategorySelector",
    "category_selector",
    "CategorySelectionResult",
]
