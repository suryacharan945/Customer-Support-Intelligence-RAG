"""Test suite for DocumentChunker and RecursiveTextSplitter validating boundaries, overlap, and determinism."""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.ingestion.loader import Document, DocumentPage
from app.ingestion.chunker import DocumentChunker, RecursiveTextSplitter, TextChunk


def create_sample_doc(
    content: str,
    doc_id: str = "doc_prod_123456789012",
    doc_type: str = "md",
    category: str = "product_manual",
    pages: list = None,
) -> Document:
    return Document(
        document_id=doc_id,
        filename="test_manual.md",
        document_type=doc_type,
        category=category,
        content_hash="hash12345678901234567890",
        source="test_manual.md",
        content=content,
        pages=pages or [DocumentPage(page_number=1, text=content)],
        total_pages=len(pages) if pages else 1,
        ingestion_timestamp="2026-10-26T00:00:00Z",
        processing_status="SUCCESS",
        file_size_bytes=len(content.encode("utf-8")),
    )


def test_deterministic_document_ids():
    """11. Test that identical content produces deterministic document IDs."""
    from app.ingestion.loader import DocumentLoader
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "test.txt"
        p.write_text("Stable deterministic text for ApexPrint ProX-400.", encoding="utf-8")

        loader = DocumentLoader()
        doc1 = loader.load_file(p, category="product_manual")
        doc2 = loader.load_file(p, category="product_manual")

        assert doc1.document_id == doc2.document_id
        assert doc1.content_hash == doc2.content_hash
        assert doc1.document_id.startswith("doc_prod_")


def test_deterministic_chunk_ids():
    """12. Test that identical text chunks receive deterministic, unique chunk IDs."""
    content = "Paragraph 1: Setup.\n\nParagraph 2: Network.\n\nParagraph 3: Maintenance."
    doc = create_sample_doc(content, doc_id="doc_prod_aabbccddeeff")

    chunker = DocumentChunker(chunk_size=30, chunk_overlap=10)
    chunks1 = chunker.chunk_document(doc)
    chunks2 = chunker.chunk_document(doc)

    assert len(chunks1) > 0
    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.content_hash == c2.content_hash
        assert c1.chunk_id.startswith("doc_prod_aabbccddeeff_c")


def test_chunk_overlap_behavior():
    """13. Test chunk overlap behavior."""
    text = (
        "Alpha section begins here. This is continuous information for testing overlap. "
        "Beta section begins here. This verifies that consecutive chunks share boundary words. "
        "Gamma section continues here with additional details."
    )
    chunker = DocumentChunker(chunk_size=80, chunk_overlap=25)
    doc = create_sample_doc(text)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    # Check that adjacent chunks share overlapping text
    c0_tail = chunks[0].text[-20:].strip()
    c1_head = chunks[1].text[:40].strip()
    # At least some tokens in the tail of chunk 0 should appear in chunk 1
    shared_tokens = set(c0_tail.split()).intersection(set(c1_head.split()))
    assert len(shared_tokens) > 0


def test_short_documents():
    """14. Test that short documents produce exactly one chunk without error."""
    short_text = "ApexPrint ProX-400 Ready."
    doc = create_sample_doc(short_text)
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert chunks[0].text == short_text
    assert chunks[0].chunk_index == 0
    assert chunks[0].char_count == len(short_text)


def test_long_documents():
    """15. Test that long documents are split cleanly into multiple chunks."""
    long_text = "\n\n".join([f"Section {i}: Detailed diagnostic instruction block {i * 10}." for i in range(100)])
    doc = create_sample_doc(long_text)

    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 5
    for c in chunks:
        assert len(c.text) <= 550  # Allows slight margin for sentence boundary
        assert c.chunk_id is not None
        assert c.document_id == doc.document_id


def test_unicode_text_handling():
    """16. Test that multilingual Unicode characters and symbols are preserved accurately."""
    unicode_content = (
        "ApexPrint Support 日本語 • Défaillance thermique: 85°C ± 2°C • "
        "Drucker-Handbuch • Предупреждение об ошибке • © 2026 ApexPrint Corp."
    )
    doc = create_sample_doc(unicode_content)
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert "日本語" in chunks[0].text
    assert "85°C" in chunks[0].text
    assert "Предупреждение" in chunks[0].text
    assert "©" in chunks[0].text


def test_pdf_page_scoped_chunk_ids():
    """Test that multi-page PDF chunks include page numbers in their deterministic chunk IDs."""
    pages = [
        DocumentPage(page_number=1, text="Page 1: Specifications for ProX-400 laser engine."),
        DocumentPage(page_number=2, text="Page 2: Maintenance and roller cleaning instructions."),
    ]
    doc = create_sample_doc("Full text", doc_id="doc_prod_998877665544", doc_type="pdf", pages=pages)

    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].chunk_id == "doc_prod_998877665544_p1_c0000"
    assert chunks[1].page_number == 2
    assert chunks[1].chunk_id == "doc_prod_998877665544_p2_c0000"


def test_whitespace_normalization():
    """Test that excessive tabs and spaces are cleaned while preserving paragraph structure."""
    messy_text = "Line 1 with    multiple    spaces.\n\n\n\nLine 2 after quadruple newline."
    doc = create_sample_doc(messy_text)
    chunker = DocumentChunker(chunk_size=1000, chunk_overlap=200)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    assert "multiple spaces" in chunks[0].text
    assert "\n\n\n\n" not in chunks[0].text
    assert "\n\n" in chunks[0].text
