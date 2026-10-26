"""Vector Store Retrieval Adapter with ChromaDB support and explicit error handling."""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.embeddings import BaseEmbeddingProvider
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
    Manages vector index queries against local ephemeral cache or restored snapshots.
    Never silently falls back to mock data unless explicitly configured in test mode.
    """

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        allow_mock: Optional[bool] = None,
    ):
        self.persist_directory = persist_directory or settings.LOCAL_EPHEMERAL_CHROMA_DIR
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK
        self.embedding_provider = embedding_provider
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
            # Use cosine distance space
            self._collection = self._client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB persistent client initialized for collection: {self.collection_name}")
        except ImportError:
            self._client = None
            self._collection = None
            if self.allow_mock:
                logger.warning("ChromaDB not installed. Operating in explicitly configured mock mode.")
            else:
                logger.info("ChromaDB library not installed. Vector store uninitialized.")
        except Exception as e:
            self._client = None
            self._collection = None
            logger.error(f"Failed to initialize ChromaDB client: {e}")

    def upsert_chunks(
        self,
        chunks: List[Any],
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> int:
        """
        Upsert a batch of TextChunks into the ChromaDB collection.
        Generates embeddings using provided provider or self.embedding_provider.
        """
        if not self._client or not self._collection:
            raise VectorStoreNotInitializedError(
                "Cannot upsert chunks: vector store client or collection is uninitialized."
            )
        if not chunks:
            return 0

        provider = embedding_provider or self.embedding_provider
        if not provider:
            raise VectorStoreError(
                "Cannot upsert chunks without an embedding provider to generate dense vectors."
            )

        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        metadatas = [
            {
                "document_id": c.document_id,
                "chunk_id": c.chunk_id,
                "category": c.category,
                "filename": c.metadata.get("filename", "") if hasattr(c, "metadata") and c.metadata else "",
                "page_number": c.page_number if c.page_number is not None else -1,
                "source": c.source,
                "content_hash": c.content_hash,
            }
            for c in chunks
        ]

        logger.info(f"Generating embeddings for {len(chunks)} chunks via {provider.model_name}...")
        embeddings = provider.embed_documents(texts)

        self._collection.upsert(
            ids=ids,
            documents=texts,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info(f"Successfully upserted {len(chunks)} chunks into ChromaDB collection '{self.collection_name}'.")
        return len(chunks)

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Query vector database for nearest semantic neighbors with optional category filtering.
        Raises VectorStoreNotInitializedError if uninitialized and mock mode is disabled.
        Raises VectorStoreQueryError if the backend query fails.
        Returns empty list if index has zero matches or is empty.
        """
        start_time = time.perf_counter()
        results: List[RetrievalResult] = []

        if self._client and self._collection:
            try:
                # Check for empty collection
                if self._collection.count() == 0:
                    logger.warning(f"ChromaDB collection '{self.collection_name}' is empty.")
                    return []

                # Build where filter if category is specified
                where_clause = {"category": category} if category else None

                # Generate query vector if embedding provider is available
                query_embeddings = None
                query_texts = None
                if self.embedding_provider:
                    query_embeddings = [self.embedding_provider.embed_query(query)]
                else:
                    query_texts = [query]

                query_kwargs: Dict[str, Any] = {
                    "n_results": min(top_k, self._collection.count()),
                }
                if query_embeddings is not None:
                    query_kwargs["query_embeddings"] = query_embeddings
                else:
                    query_kwargs["query_texts"] = query_texts

                if where_clause:
                    query_kwargs["where"] = where_clause

                raw_res = self._collection.query(**query_kwargs)

                docs = raw_res.get("documents", [[]])[0]
                metas = raw_res.get("metadatas", [[]])[0]
                distances = raw_res.get("distances", [[]])[0]
                ids = raw_res.get("ids", [[]])[0]

                latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

                for doc_id, doc_text, meta, dist in zip(ids, docs, metas, distances):
                    meta = meta or {}
                    # Cosine distance: similarity = 1.0 - distance
                    similarity = 1.0 - (dist if dist is not None else 0.5)
                    meta_copy = {**meta, "retrieval_latency_ms": latency_ms, "raw_distance": dist}
                    results.append(
                        RetrievalResult(
                            document_id=doc_id,
                            text=doc_text,
                            score=max(0.0, min(1.0, similarity)),
                            source=meta.get("source", "unknown"),
                            metadata=meta_copy,
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

    def count(self) -> int:
        """Return total chunks count in active collection."""
        if self._collection:
            return self._collection.count()
        return 0
