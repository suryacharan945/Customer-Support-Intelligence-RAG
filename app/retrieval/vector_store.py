"""Vector Store Retrieval Adapter with ChromaDB/FAISS support and graceful fallback."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.core.config import settings
from app.core.logging import logger


class VectorStoreRetriever(BaseRetriever):
    """
    Manages vector index queries against local ephemeral cache or Google Drive dumps.
    """

    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or settings.LOCAL_EPHEMERAL_CHROMA_DIR
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
            logger.warning("ChromaDB library not installed. VectorStoreRetriever operating in mock mode.")
            self._client = None

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalResult]:
        """Query vector database for nearest semantic neighbors."""
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

        # Fallback / mock retrieval for development mode
        results.append(
            RetrievalResult(
                document_id="mock_doc_1",
                text="To perform a factory reset, hold the power button for 10 seconds until the LED flashes orange.",
                score=0.92,
                source="printer_troubleshooting_guide.md",
                metadata={"category": "troubleshooting", "section": "reset"},
            )
        )
        return results
