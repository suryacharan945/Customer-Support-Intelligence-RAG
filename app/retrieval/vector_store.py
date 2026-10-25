"""Vector Store Retrieval Adapter with ChromaDB support and explicit error handling."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.core.config import settings
from app.core.logging import logger


class VectorStoreError(Exception):
    """Base exception for vector store operations."""
    pass


class VectorStoreNotInitializedError(VectorStoreError):
    """Raised when the vector store backend is not initialized and mock mode is off."""
    pass


class VectorStoreQueryError(VectorStoreError):
    """Raised when an active vector store query fails."""
    pass


class VectorStoreRetriever(BaseRetriever):
    """
    Manages vector index queries against local ephemeral cache or Google Drive dumps.
    Never silently falls back to mock data unless explicitly configured.
    """

    def __init__(self, persist_directory: Optional[str] = None, allow_mock: Optional[bool] = None):
        self.persist_directory = persist_directory or settings.LOCAL_EPHEMERAL_CHROMA_DIR
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK
        self._client = None
        self._collection = None
        self._init_client()

    def _init_client(self):
        """Lazily initialize vector store client if library is installed."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            self._collection = self._client.get_or_create_collection("customer_support_kb")
            logger.info("ChromaDB persistent client initialized successfully.")
        except ImportError:
            self._client = None
            if self.allow_mock:
                logger.warning("ChromaDB not installed. Operating in explicitly configured mock mode.")
            else:
                logger.info("ChromaDB library not installed. Vector store uninitialized.")

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Query vector database for nearest semantic neighbors.
        Raises VectorStoreNotInitializedError if uninitialized and mock mode is disabled.
        Raises VectorStoreQueryError if the backend query fails.
        Returns empty list if index has zero matches.
        """
        results: List[RetrievalResult] = []

        if self._client and self._collection:
            try:
                raw_res = self._collection.query(
                    query_texts=[query],
                    n_results=top_k,
                )
                docs = raw_res.get("documents", [[]])[0]
                metas = raw_res.get("metadatas", [[]])[0]
                distances = raw_res.get("distances", [[]])[0]
                ids = raw_res.get("ids", [[]])[0]

                for doc_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
                    similarity = 1.0 - (dist if dist is not None else 0.5)
                    results.append(
                        RetrievalResult(
                            document_id=doc_id,
                            text=doc_text,
                            score=max(0.0, similarity),
                            source=meta.get("source", "unknown"),
                            metadata=meta,
                        )
                    )
                return results
            except Exception as e:
                logger.error(f"Error querying ChromaDB: {e}")
                raise VectorStoreQueryError(f"ChromaDB query execution failed: {e}") from e

        # Handle uninitialized vector store
        if self.allow_mock:
            logger.warning("[MOCK RETRIEVAL] Returning synthetic test passage under explicitly enabled mock mode.")
            results.append(
                RetrievalResult(
                    document_id="mock_test_doc_001",
                    text="To perform a factory reset, hold the power button for 10 seconds until the LED flashes orange.",
                    score=0.92,
                    source="printer_troubleshooting_guide.md",
                    metadata={"category": "troubleshooting", "section": "reset", "is_mock": True},
                )
            )
            return results

        raise VectorStoreNotInitializedError(
            "Vector database is uninitialized or ChromaDB is not installed. "
            "Silent fallback to mock passages is prohibited in this mode."
        )
