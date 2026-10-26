"""Test suite for VectorStoreRetriever: insertion, deduplication, collection counts, metadata, and category filtering."""

from typing import List, Dict, Any, Optional
from unittest.mock import MagicMock
import pytest

from app.retrieval.vector_store import (
    VectorStoreRetriever,
    VectorStoreError,
    VectorStoreNotInitializedError,
    VectorStoreQueryError,
)
from app.retrieval.embeddings import MockEmbeddingProvider
from app.ingestion.chunker import TextChunk


class FakeChromaCollection:
    """In-memory duck-typed ChromaDB collection for isolated unit testing."""

    def __init__(self, name: str = "test_kb", metadata: Optional[Dict[str, Any]] = None):
        self.name = name
        self.metadata = metadata or {}
        self.items: Dict[str, Dict[str, Any]] = {}

    def count(self) -> int:
        return len(self.items)

    def upsert(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ):
        for cid, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
            self.items[cid] = {
                "id": cid,
                "document": doc,
                "metadata": meta,
                "embedding": emb,
            }

    def query(
        self,
        query_embeddings: Optional[List[List[float]]] = None,
        query_texts: Optional[List[str]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        matched = list(self.items.values())
        if where:
            for k, v in where.items():
                matched = [m for m in matched if m["metadata"].get(k) == v]

        matched = matched[:n_results]

        ids = [[m["id"] for m in matched]]
        docs = [[m["document"] for m in matched]]
        metas = [[m["metadata"] for m in matched]]
        # Assign dummy cosine distances
        distances = [[0.15 + (i * 0.1) for i in range(len(matched))]]

        return {
            "ids": ids,
            "documents": docs,
            "metadatas": metas,
            "distances": distances,
        }


def create_test_chunk(chunk_id: str, doc_id: str, text: str, category: str, page: Optional[int] = None) -> TextChunk:
    return TextChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        chunk_index=0,
        text=text,
        category=category,
        source=f"{doc_id}.md",
        page_number=page,
        content_hash="hash_" + chunk_id,
        metadata={"filename": f"{doc_id}.md"},
    )


def test_deterministic_indexing_ids():
    """3. Test that chunk IDs remain deterministic and distinct."""
    c1 = create_test_chunk("doc_prod_001_c0000", "doc_prod_001", "Manual content", "product_manual")
    c2 = create_test_chunk("doc_prod_001_p1_c0000", "doc_prod_001", "Page 1 content", "product_manual", page=1)

    assert c1.chunk_id == "doc_prod_001_c0000"
    assert c2.chunk_id == "doc_prod_001_p1_c0000"
    assert c1.chunk_id != c2.chunk_id


def test_uninitialized_vector_store_raises_error():
    """10. Test that uninitialized vector store raises VectorStoreNotInitializedError."""
    retriever = VectorStoreRetriever(allow_mock=False)
    retriever._client = None
    retriever._collection = None

    with pytest.raises(VectorStoreNotInitializedError):
        retriever.retrieve("Any query")


def test_mock_isolation_prohibits_silent_fallbacks():
    """13. Test that mock passages are never returned when allow_mock=False."""
    retriever = VectorStoreRetriever(allow_mock=False)
    retriever._client = None
    retriever._collection = None

    with pytest.raises(VectorStoreNotInitializedError):
        retriever.retrieve("How to reset printer?")


def test_empty_collection_returns_empty_list():
    """11. Test that querying an empty collection returns an empty list without crashing."""
    retriever = VectorStoreRetriever(allow_mock=True)
    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    results = retriever.retrieve("Any query")
    assert results == []
    assert retriever.count() == 0


def test_chromadb_insertion_and_counts():
    """4 & 6. Test upserting chunks into ChromaDB collection and verifying counts."""
    embed_provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=embed_provider)

    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunks = [
        create_test_chunk("doc_prod_01_c00", "doc_prod_01", "Specs: 45 ppm speed.", "product_manual"),
        create_test_chunk("doc_trou_01_c00", "doc_trou_01", "Fix Wi-Fi connectivity.", "troubleshooting"),
        create_test_chunk("doc_warr_01_c00", "doc_warr_01", "Warranty 1 year limited.", "warranty"),
    ]

    count = retriever.upsert_chunks(chunks)
    assert count == 3
    assert retriever.count() == 3


def test_duplicate_prevention_on_upsert():
    """5. Test that upserting duplicate chunk IDs updates in-place rather than creating duplicates."""
    embed_provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=embed_provider)

    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunks1 = [create_test_chunk("doc_prod_01_c00", "doc_prod_01", "Original text", "product_manual")]
    retriever.upsert_chunks(chunks1)
    assert retriever.count() == 1

    # Re-upsert with same chunk_id but updated text
    chunks2 = [create_test_chunk("doc_prod_01_c00", "doc_prod_01", "Updated text", "product_manual")]
    retriever.upsert_chunks(chunks2)
    assert retriever.count() == 1
    assert fake_coll.items["doc_prod_01_c00"]["document"] == "Updated text"


def test_category_filtering():
    """7. Test that retrieval with category filter returns only matches from that category."""
    embed_provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=embed_provider)

    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunks = [
        create_test_chunk("doc_prod_01_c00", "doc_prod_01", "Manual content", "product_manual"),
        create_test_chunk("doc_warr_01_c00", "doc_warr_01", "Warranty policy", "warranty"),
        create_test_chunk("doc_trou_01_c00", "doc_trou_01", "Troubleshooting guide", "troubleshooting"),
    ]
    retriever.upsert_chunks(chunks)

    # Filter by warranty
    results = retriever.retrieve("policy info", top_k=5, category="warranty")
    assert len(results) == 1
    assert results[0].metadata["category"] == "warranty"
    assert results[0].document_id == "doc_warr_01_c00"


def test_top_k_retrieval_limit():
    """8. Test that top_k restricts maximum number of returned results."""
    embed_provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=embed_provider)

    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunks = [create_test_chunk(f"doc_{i:02d}_c00", f"doc_{i:02d}", f"Text {i}", "faq") for i in range(10)]
    retriever.upsert_chunks(chunks)
    assert retriever.count() == 10

    results = retriever.retrieve("query", top_k=3)
    assert len(results) == 3


def test_metadata_preservation():
    """9. Test that metadata fields are preserved accurately in retrieval results."""
    embed_provider = MockEmbeddingProvider(allow_mock=True)
    retriever = VectorStoreRetriever(allow_mock=True, embedding_provider=embed_provider)

    fake_coll = FakeChromaCollection()
    retriever._client = MagicMock()
    retriever._collection = fake_coll

    chunk = create_test_chunk("doc_prod_5106_p1_c00", "doc_prod_5106", "Laser specs", "product_manual", page=1)
    retriever.upsert_chunks([chunk])

    res = retriever.retrieve("Laser specs", top_k=1)
    assert len(res) == 1
    m = res[0].metadata
    assert m["document_id"] == "doc_prod_5106"
    assert m["chunk_id"] == "doc_prod_5106_p1_c00"
    assert m["category"] == "product_manual"
    assert m["page_number"] == 1
    assert m["filename"] == "doc_prod_5106.md"
    assert m["content_hash"] == "hash_doc_prod_5106_p1_c00"
    assert "retrieval_latency_ms" in m


def test_retrieval_failure_handling():
    """12. Test that a failure inside ChromaDB query raises VectorStoreQueryError."""
    retriever = VectorStoreRetriever(allow_mock=True)
    mock_coll = MagicMock()
    mock_coll.count.return_value = 5
    mock_coll.query.side_effect = RuntimeError("Disk I/O failure in vector index")

    retriever._client = MagicMock()
    retriever._collection = mock_coll

    with pytest.raises(VectorStoreQueryError) as exc_info:
        retriever.retrieve("Any query")
    assert "ChromaDB query execution failed" in str(exc_info.value)
