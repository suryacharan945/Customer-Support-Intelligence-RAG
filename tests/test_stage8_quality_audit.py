"""Stage 8 Automated Quality Audit, Citation Precision, and Latency Telemetry Test Suite.

Verifies:
1. Exact separation of Citation Precision from Context Utilization.
2. Detection and reporting of unsupported or fabricated citations.
3. Accurate deduplication of repeated citations in generated answers.
4. Token compaction and whitespace normalization in MCP context assembly.
5. Cross-category conflict detection and note generation.
6. Granular sub-millisecond pipeline timing telemetry in QueryResponse.
7. Integrity and data separation of the held-out evaluation dataset.
"""

import json
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock

from app.retrieval.base import RetrievalResult
from app.generation.citation_validator import citation_validator, CitationValidationReport
from app.generation.mcp_context import MCPContextBuilder, ContextAssemblyResult
from app.generation.llm_client import LLMClient
from app.services.rag_service import RAGService
from app.api.endpoints.rag import QueryResponse


# ==============================================================================
# 1. Citation Precision vs Context Utilization Separation Tests
# ==============================================================================

def test_citation_precision_vs_context_utilization():
    """
    Verify the fundamental distinction between:
    - Citation Precision: Approved citations / Asserted model citations
    - Context Utilization: Approved citations / Retrieved candidate chunks
    """
    # 5 retrieved candidate chunks (typical MCP retrieval)
    retrieved = [
        RetrievalResult("d1", "The print speed is 45 ppm for monochrome documents.", 0.9, "manual.md", metadata={"chunk_id": "c1", "filename": "manual.md", "page_number": 1}),
        RetrievalResult("d2", "Error E-101 requires cleaning rollers with isopropyl alcohol.", 0.85, "trouble.md", metadata={"chunk_id": "c2", "filename": "trouble.md", "page_number": 2}),
        RetrievalResult("d3", "Standard limited warranty coverage is 12 months.", 0.80, "warranty.md", metadata={"chunk_id": "c3", "filename": "warranty.md", "page_number": 1}),
        RetrievalResult("d4", "Factory reset requires holding power button.", 0.75, "faq.md", metadata={"chunk_id": "c4", "filename": "faq.md", "page_number": 1}),
        RetrievalResult("d5", "Power rating is 480 Watts active printing.", 0.70, "specs.md", metadata={"chunk_id": "c5", "filename": "specs.md", "page_number": 3}),
    ]

    # Model answer cites only 2 of the 5 chunks, but both citations are 100% valid
    answer = (
        "The print speed is 45 ppm [Source: manual.md, Page: 1]. "
        "Error E-101 requires cleaning rollers [Source: trouble.md, Page: 2]."
    )

    report: CitationValidationReport = citation_validator.validate_answer(answer, retrieved)

    # In Stage 7B, the naive benchmark divided 2 / 5 = 0.40 (40%) and called it "precision".
    # In Stage 8, we correctly identify:
    # Context Utilization = 2 / 5 = 0.40 (40% of candidate chunks were used)
    # Citation Precision = 2 / 2 = 1.0 (100% of asserted citations are verified)
    assert report.retrieved_evidence_count == 5
    assert report.model_generated_citations_count == 2
    assert report.validator_approved_citations_count == 2
    assert report.unsupported_citations_count == 0
    assert report.citation_precision == 1.0
    assert report.context_utilization == 0.40
    assert report.evidence_status == "SUFFICIENT"


def test_detection_of_unsupported_citations():
    """Verify that hallucinated source filenames or wrong pages reduce citation precision."""
    retrieved = [
        RetrievalResult("d1", "Real manual text with 45 ppm print speed.", 0.95, "manual.md", metadata={"chunk_id": "c1", "filename": "manual.md", "page_number": 1}),
    ]

    # Model asserts one real citation and one completely fabricated citation
    answer = (
        "Normal operation is 45 ppm [Source: manual.md, Page: 1]. "
        "Laser diodes have lifetime coverage [Source: fake_warranty_policy.md, Page: 99]."
    )

    report = citation_validator.validate_answer(answer, retrieved)

    assert report.model_generated_citations_count == 2
    assert report.validator_approved_citations_count == 1
    assert report.unsupported_citations_count == 1
    assert len(report.unverified_citations) == 1
    assert "fake_warranty_policy.md" in report.unverified_citations[0]
    # Precision should be 1 / (1 + 1) = 0.50
    assert report.citation_precision == 0.50
    assert report.evidence_status == "PARTIAL"


def test_duplicate_citation_deduplication():
    """Verify that repeating the same citation multiple times does not inflate verified chunk count."""
    retrieved = [
        RetrievalResult("d1", "Manual content specifies speed 45 ppm and tray capacity of 500 sheets.", 0.95, "manual.md", metadata={"chunk_id": "c1", "filename": "manual.md", "page_number": 1}),
    ]

    # Model cites the same source and page twice
    answer = (
        "Speed is 45 ppm [Source: manual.md, Page: 1]. "
        "Tray capacity is 500 sheets [Source: manual.md, Page: 1]."
    )

    report = citation_validator.validate_answer(answer, retrieved)

    assert report.model_generated_citations_count == 2
    assert len(report.verified_citations) == 1  # Deduplicated verified citation objects
    assert report.citation_precision == 1.0
    assert report.unsupported_citations_count == 0


# ==============================================================================
# 2. MCP Context Assembly, Compaction and Conflict Detection Tests
# ==============================================================================

def test_mcp_whitespace_compaction():
    """Verify that excessive consecutive whitespace is compacted to reduce token footprint."""
    noisy_text = "Line 1\n\n\n\n\nLine 2\n\n\n   \n\nLine 3"
    sanitized = MCPContextBuilder.sanitize_untrusted_text(noisy_text)

    # Should not have more than two consecutive newlines
    assert "\n\n\n" not in sanitized
    assert "Line 1\n\nLine 2\n\nLine 3" == sanitized


def test_cross_category_conflict_notes_and_flag():
    """Verify that coexisting troubleshooting and warranty contexts trigger conflict notice."""
    chunks = [
        RetrievalResult("d1", "Disassemble fuser to clean rollers.", 0.9, "t.md", metadata={"chunk_id": "c1", "category": "troubleshooting"}),
        RetrievalResult("d2", "Disassembly by unauthorized personnel voids warranty.", 0.85, "w.md", metadata={"chunk_id": "c2", "category": "warranty"}),
    ]

    result: ContextAssemblyResult = MCPContextBuilder.build_context(chunks)

    assert result.has_potential_conflict is True
    assert result.conflict_notes is not None
    assert "Multi-Context Notice" in result.conflict_notes
    assert "warranty" in result.categories_represented
    assert "troubleshooting" in result.categories_represented


# ==============================================================================
# 3. Pipeline Timing Telemetry Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_granular_timing_breakdown_in_query_response():
    """Verify that QueryResponse contains a complete, non-negative timing breakdown dictionary."""
    mock_llm = MagicMock(spec=LLMClient)
    mock_llm.generate_response = AsyncMock(return_value={
        "text": "Print speed is 45 ppm [Source: manual.md, Page: 1].",
        "provider": "mock",
        "is_mock": True,
    })

    rag = RAGService(llm_client=mock_llm, allow_mock=True)

    # Execute query in multi-context mode
    resp: QueryResponse = await rag.process_query(
        "What is the print speed of the ProX-400?",
        retrieval_mode="multi_context",
    )

    assert resp.timing_breakdown is not None
    tb = resp.timing_breakdown

    required_timing_keys = [
        "category_selection_ms",
        "query_expansion_ms",
        "retrieval_dense_ms",
        "retrieval_sparse_ms",
        "retrieval_fusion_ms",
        "retrieval_total_ms",
        "context_assembly_ms",
        "llm_generation_ms",
        "citation_validation_ms",
        "total_pipeline_ms",
    ]

    for key in required_timing_keys:
        assert key in tb, f"Missing key '{key}' in timing_breakdown"
        assert isinstance(tb[key], (int, float)), f"Value for '{key}' must be numeric"
        assert tb[key] >= 0.0, f"Latency '{key}' cannot be negative"

    # Execution time must match total_pipeline_ms
    assert resp.execution_time_ms == tb["total_pipeline_ms"]
    assert resp.citation_precision is not None
    assert resp.context_utilization is not None


@pytest.mark.asyncio
async def test_empty_retrieval_timing_telemetry():
    """Verify timing telemetry when zero matching contexts are retrieved."""
    mock_llm = MagicMock(spec=LLMClient)
    rag = RAGService(llm_client=mock_llm, allow_mock=True)

    # Force empty retrieval
    rag.hybrid_retriever.retrieve = MagicMock(return_value=[])

    resp: QueryResponse = await rag.process_query(
        "Query with zero results",
        retrieval_mode="baseline",
    )

    assert resp.evidence_status == "INSUFFICIENT"
    assert resp.timing_breakdown is not None
    assert resp.timing_breakdown["retrieval_total_ms"] >= 0.0
    assert resp.timing_breakdown["total_pipeline_ms"] >= 0.0
    assert resp.citation_precision == 1.0
    assert resp.context_utilization == 0.0


# ==============================================================================
# 4. Held-Out Evaluation Dataset Integrity Tests
# ==============================================================================

def test_held_out_dataset_integrity_and_data_separation():
    """Verify that held_out_dataset.json is structurally valid and completely disjoint from Stage 7B dev set."""
    held_out_path = Path("evaluation/held_out_dataset.json")
    assert held_out_path.exists(), "Held-out evaluation dataset does not exist"

    with open(held_out_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "held_out_queries" in data
    queries = data["held_out_queries"]
    assert len(queries) == 10, f"Expected 10 held-out queries, found {len(queries)}"

    held_out_ids = {q["query_id"] for q in queries}
    held_out_texts = {q["query"].strip().lower() for q in queries}

    # Load development queries from stage7b_live_results.json
    dev_path = Path("evaluation/stage7b_live_results.json")
    with open(dev_path, "r", encoding="utf-8") as f:
        dev_data = json.load(f)

    dev_queries = dev_data["queries_benchmark_results"]
    dev_ids = {q["query_id"] for q in dev_queries}
    dev_texts = {q["query"].strip().lower() for q in dev_queries}

    # Strict zero-overlap checks
    overlap_ids = held_out_ids.intersection(dev_ids)
    overlap_texts = held_out_texts.intersection(dev_texts)

    assert len(overlap_ids) == 0, f"Query ID leakage detected: {overlap_ids}"
    assert len(overlap_texts) == 0, f"Query text leakage detected: {overlap_texts}"

    # Verify query schema
    for q in queries:
        assert "query_id" in q
        assert "query" in q
        assert "domain_category" in q
        assert "expected_sources" in q
        assert "ground_truth_claims" in q
        assert len(q["ground_truth_claims"]) > 0
