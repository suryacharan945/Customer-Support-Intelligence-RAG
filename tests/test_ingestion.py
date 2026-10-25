"""Test suite for DocumentLoader validating format support, metadata integrity, and error boundaries."""

import io
import sys
import tempfile
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.ingestion.loader import (
    DocumentLoader,
    Document,
    EmptyDocumentError,
    CorruptedFileError,
    UnsupportedFileTypeError,
    OversizedFileError,
    InvalidCategoryError,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def test_txt_loading(temp_dir):
    """3. Test valid UTF-8 TXT loading."""
    txt_file = temp_dir / "sample.txt"
    txt_file.write_text("This is an ApexPrint printer troubleshooting guide.", encoding="utf-8")

    loader = DocumentLoader()
    doc = loader.load_file(txt_file, category="troubleshooting")

    assert isinstance(doc, Document)
    assert doc.document_type == "txt"
    assert doc.category == "troubleshooting"
    assert doc.filename == "sample.txt"
    assert "troubleshooting guide" in doc.content
    assert doc.total_pages == 1
    assert len(doc.pages) == 1
    assert doc.pages[0].page_number == 1
    assert doc.processing_status == "SUCCESS"


def test_markdown_loading(temp_dir):
    """4. Test Markdown loading."""
    md_file = temp_dir / "manual.md"
    md_file.write_text("# User Manual\n\n## Section 1: Setup\nConnect power cable.", encoding="utf-8")

    loader = DocumentLoader()
    doc = loader.load_file(md_file, category="product_manual")

    assert doc.document_type == "md"
    assert doc.category == "product_manual"
    assert doc.total_pages == 1
    assert "Connect power cable" in doc.content


def test_valid_pdf_extraction_and_page_metadata(temp_dir):
    """1 & 2. Test valid multi-page PDF extraction and page metadata preservation."""
    from reportlab.pdfgen import canvas
    pdf_file = temp_dir / "test_multipage.pdf"

    c = canvas.Canvas(str(pdf_file))
    c.drawString(100, 700, "ApexPrint Page 1: Power Management Specifications")
    c.showPage()
    c.drawString(100, 700, "ApexPrint Page 2: Maintenance and Roller Replacement")
    c.showPage()
    c.save()

    loader = DocumentLoader()
    doc = loader.load_file(pdf_file, category="product_manual")

    assert doc.document_type == "pdf"
    assert doc.total_pages == 2
    assert len(doc.pages) == 2
    assert doc.pages[0].page_number == 1
    assert "Page 1" in doc.pages[0].text
    assert doc.pages[1].page_number == 2
    assert "Page 2" in doc.pages[1].text
    assert "Power Management" in doc.content
    assert "Roller Replacement" in doc.content


def test_empty_document_rejection(temp_dir):
    """5. Test empty document rejection (0 bytes and whitespace only)."""
    empty_file = temp_dir / "empty.txt"
    empty_file.write_bytes(b"")

    loader = DocumentLoader()
    with pytest.raises(EmptyDocumentError) as exc:
        loader.load_file(empty_file, category="faq")
    assert "is empty (0 bytes)" in str(exc.value)

    whitespace_file = temp_dir / "whitespace.txt"
    whitespace_file.write_text("   \n\n  \t  \n  ", encoding="utf-8")
    with pytest.raises(EmptyDocumentError) as exc2:
        loader.load_file(whitespace_file, category="faq")
    assert "contains only whitespace" in str(exc2.value)


def test_corrupted_pdf_handling(temp_dir):
    """6. Test corrupted PDF file error handling."""
    corrupted_pdf = temp_dir / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"%PDF-1.4 \n garbage random binary bytes not valid pdf structure")

    loader = DocumentLoader()
    with pytest.raises(CorruptedFileError) as exc:
        loader.load_file(corrupted_pdf, category="warranty")
    assert "PDF parsing failed" in str(exc.value)


def test_unsupported_file_types(temp_dir):
    """7. Test rejection of unsupported file types."""
    unsupported_file = temp_dir / "executable.exe"
    unsupported_file.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00")

    loader = DocumentLoader()
    with pytest.raises(UnsupportedFileTypeError) as exc:
        loader.load_file(unsupported_file, category="product_manual")
    assert "Unsupported file format '.exe'" in str(exc.value)


def test_invalid_encoding_handling(temp_dir):
    """8. Test invalid encoding handling (Latin-1 fallback decoding)."""
    encoded_file = temp_dir / "latin1.txt"
    # Write bytes valid in latin-1 (e.g., degree sign '\xb0' and copyright '\xa9') but invalid UTF-8
    encoded_file.write_bytes(b"ApexPrint Temperature: 85\xb0C \xa9 ApexPrint Corp.")

    loader = DocumentLoader()
    doc = loader.load_file(encoded_file, category="troubleshooting")
    assert doc.processing_status == "SUCCESS"
    assert "ApexPrint Temperature: 85" in doc.content


def test_oversized_file_rejection(temp_dir):
    """9. Test oversized file rejection."""
    oversized_file = temp_dir / "large.txt"
    oversized_file.write_bytes(b"A" * 5000)

    loader = DocumentLoader(max_file_size_bytes=4096)  # 4 KB limit
    with pytest.raises(OversizedFileError) as exc:
        loader.load_file(oversized_file, category="faq")
    assert "exceeds maximum limit" in str(exc.value)


def test_category_validation(temp_dir):
    """10. Test category metadata validation."""
    valid_file = temp_dir / "terms.md"
    valid_file.write_text("Warranty terms text", encoding="utf-8")

    loader = DocumentLoader()
    # Missing category
    with pytest.raises(InvalidCategoryError) as exc1:
        loader.load_file(valid_file, category="")
    assert "required" in str(exc1.value)

    # Invalid category
    with pytest.raises(InvalidCategoryError) as exc2:
        loader.load_file(valid_file, category="random_invalid_cat")
    assert "Invalid category" in str(exc2.value)

    # Valid category accepted
    doc = loader.load_file(valid_file, category="warranty")
    assert doc.category == "warranty"


def test_scanned_pdf_rejection(temp_dir):
    """Test rejection of scanned image PDFs containing zero text."""
    from reportlab.pdfgen import canvas
    blank_pdf = temp_dir / "blank_scanned.pdf"
    c = canvas.Canvas(str(blank_pdf))
    c.showPage()  # Empty page with no text
    c.save()

    loader = DocumentLoader(allow_scanned_pdf=False)
    with pytest.raises(EmptyDocumentError) as exc:
        loader.load_file(blank_pdf, category="troubleshooting")
    assert "contains no extractable text" in str(exc.value)
