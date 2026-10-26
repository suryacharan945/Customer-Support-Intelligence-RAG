"""Document loader module supporting PDF, TXT, and Markdown customer support assets.

Provides robust validation, page-level tracking, content hashing, and category enforcement.
"""

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

VALID_CATEGORIES = {
    "product_manual",
    "troubleshooting",
    "warranty",
    "faq",
}

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".txt": "txt",
    ".md": "md",
}


class IngestionError(Exception):
    """Base exception for document ingestion failures."""
    pass


class UnsupportedFileTypeError(IngestionError):
    """Raised when an unsupported file extension is encountered."""
    pass


class InvalidCategoryError(IngestionError):
    """Raised when document category is missing or not in allowed categories."""
    pass


class CorruptedFileError(IngestionError):
    """Raised when file reading fails due to file corruption or invalid structure."""
    pass


class OversizedFileError(IngestionError):
    """Raised when file exceeds the maximum allowed ingestion size."""
    pass


class EmptyDocumentError(IngestionError):
    """Raised when an ingested file contains zero bytes or only whitespace."""
    pass


class PathTraversalError(IngestionError):
    """Raised when an uploaded filename attempts directory traversal."""
    pass


class DocumentPage:
    """Represents a discrete page within a document (for PDFs)."""

    def __init__(self, page_number: int, text: str):
        self.page_number = page_number
        self.text = text

    def to_dict(self) -> Dict[str, Any]:
        return {
            "page_number": self.page_number,
            "text": self.text,
            "char_count": len(self.text),
        }


class Document:
    """Standardized internal representation of an ingested document with rich metadata."""

    def __init__(
        self,
        document_id: str,
        filename: str,
        document_type: str,
        category: str,
        content_hash: str,
        source: str,
        content: str,
        pages: List[DocumentPage],
        total_pages: Optional[int],
        ingestion_timestamp: str,
        processing_status: str,
        file_size_bytes: int,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.document_id = document_id
        self.filename = filename
        self.document_type = document_type
        self.category = category
        self.content_hash = content_hash
        self.source = source
        self.content = content
        self.pages = pages
        self.total_pages = total_pages
        self.ingestion_timestamp = ingestion_timestamp
        self.processing_status = processing_status
        self.file_size_bytes = file_size_bytes
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document_id": self.document_id,
            "filename": self.filename,
            "document_type": self.document_type,
            "category": self.category,
            "content_hash": self.content_hash,
            "source": self.source,
            "total_pages": self.total_pages,
            "ingestion_timestamp": self.ingestion_timestamp,
            "processing_status": self.processing_status,
            "file_size_bytes": self.file_size_bytes,
            "char_count": len(self.content),
            "page_count": len(self.pages),
            "metadata": self.metadata,
        }

    def __repr__(self):
        return (
            f"<Document id={self.document_id} type={self.document_type} "
            f"cat={self.category} status={self.processing_status} pages={self.total_pages}>"
        )


class DocumentLoader:
    """
    Robust loader supporting PDF, TXT, and Markdown documents.
    Enforces category boundaries, size limits, and stable hashing.
    """

    def __init__(
        self,
        max_file_size_bytes: int = 10 * 1024 * 1024,  # 10 MB default limit
        allow_scanned_pdf: bool = False,
    ):
        self.max_file_size_bytes = max_file_size_bytes
        self.allow_scanned_pdf = allow_scanned_pdf

    @staticmethod
    def validate_category(category: str) -> str:
        """Ensure category is strictly one of the allowed categories."""
        if not category:
            raise InvalidCategoryError("Document category is required but was not provided.")
        norm_cat = category.strip().lower()
        if norm_cat not in VALID_CATEGORIES:
            raise InvalidCategoryError(
                f"Invalid category '{category}'. Must be one of: {sorted(list(VALID_CATEGORIES))}"
            )
        return norm_cat

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Generate deterministic SHA-256 hash of raw bytes."""
        return hashlib.sha256(data).hexdigest()

    def load_file(
        self,
        file_path: str | Path,
        category: str,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Document:
        """
        Load, validate, and parse a single document file.
        Raises IngestionError subclasses on failure.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Validate file size
        file_size = path.stat().st_size
        if file_size > self.max_file_size_bytes:
            raise OversizedFileError(
                f"File '{path.name}' ({file_size:,} bytes) exceeds maximum limit "
                f"of {self.max_file_size_bytes:,} bytes."
            )

        if file_size == 0:
            raise EmptyDocumentError(f"File '{path.name}' is empty (0 bytes).")

        # Validate category
        valid_cat = self.validate_category(category)

        # Validate extension
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file format '{ext}' for file '{path.name}'. "
                f"Supported formats: {list(SUPPORTED_EXTENSIONS.keys())}"
            )

        doc_type = SUPPORTED_EXTENSIONS[ext]

        # Read raw content and hash
        raw_bytes = path.read_bytes()
        content_hash = self.compute_sha256(raw_bytes)
        doc_id = f"doc_{valid_cat[:4]}_{content_hash[:12]}"
        timestamp = datetime.now(timezone.utc).isoformat()

        if doc_type == "pdf":
            return self._load_pdf(
                path=path,
                raw_bytes=raw_bytes,
                doc_id=doc_id,
                category=valid_cat,
                content_hash=content_hash,
                timestamp=timestamp,
                file_size=file_size,
                custom_metadata=custom_metadata,
            )
        else:
            return self._load_text_based(
                path=path,
                raw_bytes=raw_bytes,
                doc_id=doc_id,
                doc_type=doc_type,
                category=valid_cat,
                content_hash=content_hash,
                timestamp=timestamp,
                file_size=file_size,
                custom_metadata=custom_metadata,
            )

    def _load_text_based(
        self,
        path: Path,
        raw_bytes: bytes,
        doc_id: str,
        doc_type: str,
        category: str,
        content_hash: str,
        timestamp: str,
        file_size: int,
        custom_metadata: Optional[Dict[str, Any]],
    ) -> Document:
        """Decode and parse text or markdown files."""
        # Try UTF-8 first, then UTF-8 with BOM, then fallback to latin-1 with warning
        text = None
        encoding_used = "utf-8"
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = raw_bytes.decode("utf-8-sig")
                encoding_used = "utf-8-sig"
            except UnicodeDecodeError:
                try:
                    text = raw_bytes.decode("latin-1")
                    encoding_used = "latin-1"
                except Exception as e:
                    raise CorruptedFileError(f"Unable to decode text file '{path.name}': {e}") from e

        if not text.strip():
            raise EmptyDocumentError(f"Text file '{path.name}' contains only whitespace.")

        pages = [DocumentPage(page_number=1, text=text)]
        meta = {
            "source_path": str(path),
            "encoding": encoding_used,
            **(custom_metadata or {}),
        }

        return Document(
            document_id=doc_id,
            filename=path.name,
            document_type=doc_type,
            category=category,
            content_hash=content_hash,
            source=path.name,
            content=text,
            pages=pages,
            total_pages=1,
            ingestion_timestamp=timestamp,
            processing_status="SUCCESS",
            file_size_bytes=file_size,
            metadata=meta,
        )

    def _load_pdf(
        self,
        path: Path,
        raw_bytes: bytes,
        doc_id: str,
        category: str,
        content_hash: str,
        timestamp: str,
        file_size: int,
        custom_metadata: Optional[Dict[str, Any]],
    ) -> Document:
        """Extract text from PDF files page-by-page."""
        try:
            import io
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(raw_bytes))
        except Exception as e:
            raise CorruptedFileError(f"PDF parsing failed for '{path.name}': {e}") from e

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise EmptyDocumentError(f"PDF '{path.name}' contains 0 pages.")

        pages: List[DocumentPage] = []
        full_text_parts: List[str] = []
        has_any_text = False

        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                page_text = ""
            
            cleaned_page_text = page_text.strip()
            if cleaned_page_text:
                has_any_text = True
            
            pages.append(DocumentPage(page_number=page_num, text=cleaned_page_text))
            if cleaned_page_text:
                full_text_parts.append(cleaned_page_text)

        full_content = "\n\n".join(full_text_parts)

        # Scanned PDF check: reject or flag if zero text extracted
        if not has_any_text:
            if not self.allow_scanned_pdf:
                raise EmptyDocumentError(
                    f"PDF '{path.name}' contains no extractable text across all {total_pages} page(s). "
                    "Scanned image PDFs are not supported without OCR."
                )
            status = "SCANNED_OR_EMPTY_PDF"
        else:
            status = "SUCCESS"

        meta = {
            "source_path": str(path),
            "pdf_pages_extracted": len(pages),
            "is_encrypted": reader.is_encrypted,
            **(custom_metadata or {}),
        }

        return Document(
            document_id=doc_id,
            filename=path.name,
            document_type="pdf",
            category=category,
            content_hash=content_hash,
            source=path.name,
            content=full_content,
            pages=pages,
            total_pages=total_pages,
            ingestion_timestamp=timestamp,
            processing_status=status,
            file_size_bytes=file_size,
            metadata=meta,
        )

    def load_directory(
        self,
        directory_path: str | Path,
        category: Optional[str] = None,
    ) -> List[Document]:
        """
        Walk a directory and load all valid supported documents.
        If category is not provided, expects subdirectories named after valid categories.
        """
        dir_path = Path(directory_path)
        if not dir_path.exists():
            return []

        documents: List[Document] = []
        for root, _, files in os.walk(dir_path):
            current_dir_name = Path(root).name.lower()
            dir_category = category or (current_dir_name if current_dir_name in VALID_CATEGORIES else None)

            for file in sorted(files):
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                if ext in SUPPORTED_EXTENSIONS:
                    if not dir_category:
                        print(f"[LOADER SKIP] Skipping {file_path.name}: No valid category assigned.")
                        continue
                    try:
                        doc = self.load_file(file_path=file_path, category=dir_category)
                        documents.append(doc)
                    except Exception as e:
                        print(f"[LOADER ERROR] Failed to load {file_path.name}: {e}")

        return documents
