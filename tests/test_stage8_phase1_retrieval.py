"""Stage 8 Phase 1 Acceptance Test Suite: Generalized Query Understanding and Soft Retrieval.

Verifies:
1. General architecture question is analyzed correctly.
2. Technology-stack question is analyzed correctly.
3. Benchmark question is analyzed correctly.
4. Question about the project dossier is not forced into printer-support categories.
5. General retrieval can retrieve chunks categorized as 'general', 'dossier', or 'engineering'.
6. Category preferences do not exclude otherwise relevant evidence in general-query mode.
7. Existing printer troubleshooting retrieval continues to work.
8. Existing warranty retrieval continues to work.
9. Existing dense retrieval behavior is not unintentionally broken.
10. Existing BM25 behavior is not unintentionally broken.
11. RRF continues to combine candidate rankings correctly.
12. Missing or uncertain category metadata is handled safely.
"""

from unittest.mock import MagicMock
import pytest

from app.retrieval.query_analyzer import QueryAnalyzer, query_analyzer
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.hybrid import HybridRetriever
from app.ingestion.chunker import TextChunk
from app.services.rag_service import RAGService


def make_test_chunk(
    chunk_id: str,
    doc_id: str,
    text: str,
    category: str,
    page: int = 1,
    source: str = "test_doc.md",
) -> TextChunk:
    return TextChunk(
        chunk_id=chunk_id,
        document_id=doc_id,
        chunk_index=0,
        text=text,
        category=category,
        source=source,
        page_number=page,
        content_hash=f"hash_{chunk_id}",
        metadata={"filename": source, "category": category, "page_number": page, "chunk_id": chunk_id},
    )


# ----------------------------------------------------------------------
# 1-4. Query Analyzer Acceptance Tests
# ----------------------------------------------------------------------

def test_query_analyzer_architecture_intent():
    """1. Test that general architecture questions are classified into architecture intent."""
    res = query_analyzer.analyze_query("Explain the complete architecture and presentation layer of this project.")
    assert res.primary_intent == "architecture"
    assert res.is_customer_support is False
    assert "presentation layer" in [s.lower() for s in res.extracted_subjects] or any("presentation" in c for c in res.intents[0].matched_cues)
    assert res.category_preferences == []
    assert res.soft_preference_only is True


def test_query_analyzer_technology_stack_intent():
    """2. Test that technology-stack questions are classified into technology_stack intent."""
    res = query_analyzer.analyze_query("What technology stack is used in the frontend and backend? Is React and FastAPI used?")
    assert res.primary_intent == "technology_stack"
    assert res.is_customer_support is False
    assert any(tech in res.extracted_subjects for tech in ["react", "fastapi"])
    assert res.category_preferences == []


def test_query_analyzer_benchmark_intent():
    """3. Test that benchmark questions are classified into benchmark_analysis intent."""
    res = query_analyzer.analyze_query("What are the benchmark results, retrieval latency, and accuracy metrics?")
    assert res.primary_intent == "benchmark_analysis"
    assert res.is_customer_support is False
    assert res.category_preferences == []


def test_query_analyzer_project_dossier_not_forced_to_printer_support():
    """4. Test that questions about the project dossier are not forced into printer support."""
    res = query_analyzer.analyze_query("How does Multi-Context Prompting work in the AI Customer Support Intelligence Platform dossier?")
    assert res.is_customer_support is False
    assert res.primary_intent in ("feature_explanation", "architecture", "general_qa")
    assert "multi-context prompting" in res.extracted_subjects
    assert res.category_preferences == []
    assert res.soft_preference_only is True


# ----------------------------------------------------------------------
# 5-6. General Retrieval & Soft Category Non-Exclusion
# ----------------------------------------------------------------------

def test_general_retrieval_retrieves_non_printer_categories():
    """5. Test that general retrieval retrieves chunks categorized as general, dossier, or engineering."""
    chunks = [
        make_test_chunk("c_arch", "doc_dossier", "System Architecture: Presentation Layer in React 18, Backend in FastAPI.", "engineering", source="project_dossier.pdf"),
        make_test_chunk("c_eval", "doc_dossier", "Benchmark Evaluation: Mode B achieved 93.3% Precision@5 and sub-second latency.", "dossier", source="project_dossier.pdf"),
        make_test_chunk("c_trou", "doc_printer", "Error E-101 Paper Jam clearing steps in Tray 1.", "troubleshooting", source="manual.md"),
    ]
    bm25 = BM25Retriever(chunks)
    mock_dense = MagicMock(spec=BaseRetriever)
    mock_dense.retrieve.return_value = [
        RetrievalResult(document_id="doc_dossier", text=chunks[0].text, score=0.92, source="project_dossier.pdf", metadata=chunks[0].metadata),
        RetrievalResult(document_id="doc_dossier", text=chunks[1].text, score=0.88, source="project_dossier.pdf", metadata=chunks[1].metadata),
    ]

    hybrid = HybridRetriever(vector_retriever=mock_dense, bm25_retriever=bm25)
    # General query: category=None, soft_category=True
    results = hybrid.retrieve("system architecture presentation layer", top_k=2, category=None, soft_category=True)

    assert len(results) >= 1
    retrieved_cats = {r.metadata.get("category") for r in results}
    assert "engineering" in retrieved_cats or "dossier" in retrieved_cats


def test_soft_category_does_not_exclude_relevant_evidence():
    """6. Test that category preferences do not exclude otherwise highly-relevant evidence in soft mode."""
    chunks = [
        make_test_chunk("c_arch", "d1", "Complete system architecture pipeline with FastAPI and React.", "engineering"),
        make_test_chunk("c_manual", "d2", "ApexPrint hardware manual specifications and dimensions.", "product_manual"),
    ]
    bm25 = BM25Retriever(chunks)
    mock_dense = MagicMock(spec=BaseRetriever)
    # Even if product_manual is given as a preference, engineering chunk has high relevance
    mock_dense.retrieve.return_value = [
        RetrievalResult(document_id="d1", text=chunks[0].text, score=0.96, source="dossier.pdf", metadata=chunks[0].metadata),
        RetrievalResult(document_id="d2", text=chunks[1].text, score=0.70, source="manual.md", metadata=chunks[1].metadata),
    ]

    hybrid = HybridRetriever(vector_retriever=mock_dense, bm25_retriever=bm25)
    # Query with soft_category=True and category=['product_manual']
    results = hybrid.retrieve("system architecture pipeline", top_k=2, category=["product_manual"], soft_category=True)

    # Chunk with 'engineering' category must NOT be excluded
    cids = [r.metadata["chunk_id"] for r in results]
    assert "c_arch" in cids


# ----------------------------------------------------------------------
# 7-8. Existing Printer Support Routing Preservation
# ----------------------------------------------------------------------

def test_existing_printer_troubleshooting_routing_preserved():
    """7. Test that printer troubleshooting queries continue to be identified as customer support."""
    res = query_analyzer.analyze_query("How do I clear error code E-101 Paper Jam in tray 2 on the ProX-400?")
    assert res.is_customer_support is True
    assert "troubleshooting" in res.category_preferences
    assert res.primary_intent == "troubleshooting"


def test_existing_printer_warranty_routing_preserved():
    """8. Test that printer warranty queries continue to be identified as customer support."""
    res = query_analyzer.analyze_query("What is the standard warranty coverage and RMA return procedure for defective hardware?")
    assert res.is_customer_support is True
    assert "warranty" in res.category_preferences
    assert res.primary_intent == "warranty_policy"


# ----------------------------------------------------------------------
# 9-11. Dense, BM25, and RRF Pipeline Integrity
# ----------------------------------------------------------------------

def test_dense_retrieval_integrity():
    """9. Test that pure dense retrieval executes without interference."""
    mock_dense = MagicMock(spec=BaseRetriever)
    mock_dense.retrieve.return_value = [
        RetrievalResult(document_id="d1", text="Dense match", score=0.91, source="doc.md", metadata={"chunk_id": "c1", "category": "general"})
    ]
    hybrid = HybridRetriever(vector_retriever=mock_dense, bm25_retriever=None)
    results = hybrid.retrieve("sample query", top_k=1, mode="dense")
    assert len(results) == 1
    assert results[0].text == "Dense match"


def test_bm25_retrieval_integrity():
    """10. Test that pure BM25 retrieval keyword scoring executes correctly."""
    chunks = [
        make_test_chunk("c1", "d1", "Reciprocal Rank Fusion merges rankings from dense and sparse retrievers.", "architecture"),
        make_test_chunk("c2", "d2", "ApexPrint toner cartridge yield is 5000 pages.", "product_manual"),
    ]
    bm25 = BM25Retriever(chunks)
    res = bm25.retrieve("Reciprocal Rank Fusion", top_k=1, mode=None) if hasattr(bm25, "mode") else bm25.retrieve("Reciprocal Rank Fusion", top_k=1)
    assert len(res) == 1
    assert res[0].metadata["chunk_id"] == "c1"


def test_rrf_combines_candidate_rankings_correctly():
    """11. Test that RRF accurately combines dense and sparse rankings and computes valid scores."""
    mock_dense = MagicMock(spec=BaseRetriever)
    mock_dense.retrieve.return_value = [
        RetrievalResult(document_id="d1", text="FastAPI backend", score=0.90, source="dossier.pdf", metadata={"chunk_id": "c1", "category": "tech"}),
        RetrievalResult(document_id="d2", text="React frontend", score=0.80, source="dossier.pdf", metadata={"chunk_id": "c2", "category": "tech"}),
    ]
    mock_sparse = MagicMock(spec=BM25Retriever)
    mock_sparse.retrieve.return_value = [
        RetrievalResult(document_id="d2", text="React frontend", score=0.95, source="dossier.pdf", metadata={"chunk_id": "c2", "category": "tech"}),
        RetrievalResult(document_id="d1", text="FastAPI backend", score=0.85, source="dossier.pdf", metadata={"chunk_id": "c1", "category": "tech"}),
    ]
    hybrid = HybridRetriever(vector_retriever=mock_dense, bm25_retriever=mock_sparse, alpha=0.5)
    results = hybrid.retrieve("FastAPI and React stack", top_k=2, mode="hybrid")

    assert len(results) == 2
    for r in results:
        assert 0.0 <= r.score <= 1.0
        assert r.metadata["retrieval_method"] == "hybrid_rrf"
        assert r.metadata["dense_rank"] in (1, 2)
        assert r.metadata["sparse_rank"] in (1, 2)


# ----------------------------------------------------------------------
# 12. Missing / Uncertain Category Handling
# ----------------------------------------------------------------------

def test_missing_or_uncertain_category_handled_safely():
    """12. Test that missing category metadata (None or empty string) does not crash retrieval."""
    chunk_no_cat = make_test_chunk("c_nocat", "d_nocat", "General knowledge documentation text without explicit category.", "")
    chunk_no_cat.category = ""
    chunk_no_cat.metadata["category"] = None

    bm25 = BM25Retriever([chunk_no_cat])
    res = bm25.retrieve("General knowledge", top_k=1, soft_category=True)
    assert len(res) == 1
    assert res[0].metadata["chunk_id"] == "c_nocat"

    # Query analyzer handling of ambiguous query
    res_qa = query_analyzer.analyze_query("Can you provide information on this topic?")
    assert res_qa.primary_intent == "general_qa"
    assert res_qa.soft_preference_only is True
    assert res_qa.category_preferences == []
