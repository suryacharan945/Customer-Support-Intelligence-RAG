"""Document ingestion, preprocessing, chunking, and manifest tracking package."""

from app.ingestion.loader import (
    Document,
    DocumentPage,
    DocumentLoader,
    IngestionError,
    UnsupportedFileTypeError,
    InvalidCategoryError,
    CorruptedFileError,
    OversizedFileError,
    EmptyDocumentError,
    VALID_CATEGORIES,
    SUPPORTED_EXTENSIONS,
)
from app.ingestion.chunker import (
    TextChunk,
    DocumentChunker,
    RecursiveTextSplitter,
)
from app.ingestion.manifest import IngestionManifest

__all__ = [
    "Document",
    "DocumentPage",
    "DocumentLoader",
    "TextChunk",
    "DocumentChunker",
    "RecursiveTextSplitter",
    "IngestionManifest",
    "IngestionError",
    "UnsupportedFileTypeError",
    "InvalidCategoryError",
    "CorruptedFileError",
    "OversizedFileError",
    "EmptyDocumentError",
    "VALID_CATEGORIES",
    "SUPPORTED_EXTENSIONS",
]
