"""Recursive document chunker with boundary preservation and deterministic chunk IDs.

Note on Chunking Strategies:
- Character-based Chunking: Operates on character counts with recursive linguistic
  separators (paragraphs, sentences, words). It is deterministic, model-agnostic,
  lightning-fast, and operates with zero extra memory or model dependencies.
- Token-based Chunking: Operates on BPE/WordPiece tokens matching a specific LLM
  vocabulary (e.g., TikToken or HuggingFace Tokenizers). It accurately respects token
  budgets for LLM context limits, but incurs additional tokenizer loading overhead.
"""

import hashlib
import re
from typing import List, Dict, Any, Optional
from app.ingestion.loader import Document, DocumentPage


class TextChunk:
    """Represents an atomic, traceable chunk of document text with rich metadata."""

    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        chunk_index: int,
        text: str,
        category: str,
        source: str,
        page_number: Optional[int],
        content_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.chunk_index = chunk_index
        self.text = text
        self.category = category
        self.source = source
        self.page_number = page_number
        self.content_hash = content_hash
        self.char_count = len(text)
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "category": self.category,
            "source": self.source,
            "page_number": self.page_number,
            "content_hash": self.content_hash,
            "char_count": self.char_count,
            "metadata": self.metadata,
        }

    def __repr__(self):
        return (
            f"<TextChunk id={self.chunk_id} doc={self.document_id} "
            f"page={self.page_number} chars={self.char_count}>"
        )


class RecursiveTextSplitter:
    """
    Recursively splits text into chunks along structural and natural language boundaries.
    Tries separators in order: double newline -> single newline -> sentence boundary -> space.
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
    ):
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly less than chunk_size ({chunk_size})"
            )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or self.DEFAULT_SEPARATORS

    def _clean_whitespace(self, text: str) -> str:
        """Normalize excessive horizontal spaces while preserving vertical line breaks."""
        # Replace 3 or more newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace multiple spaces/tabs within a line with a single space
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def split_text(self, text: str) -> List[str]:
        """Split a string into clean, overlapping character chunks."""
        cleaned = self._clean_whitespace(text)
        if not cleaned:
            return []

        # If already fits within chunk_size, return as single chunk
        if len(cleaned) <= self.chunk_size:
            return [cleaned]

        return self._recursive_split(cleaned, self.separators)

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        """Core recursive splitting algorithm."""
        final_chunks: List[str] = []
        separator = separators[-1]
        new_separators = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator != "" else list(text)

        good_splits: List[str] = []
        for s in splits:
            if s.strip():
                good_splits.append(s.strip())

        # Merge splits up to chunk_size with overlap
        current_doc: List[str] = []
        total_len = 0

        for s in good_splits:
            s_len = len(s) + (len(separator) if current_doc else 0)
            if total_len + s_len > self.chunk_size:
                if current_doc:
                    doc_text = separator.join(current_doc).strip()
                    if doc_text:
                        final_chunks.append(doc_text)
                    # Handle overlap: retain elements from end of current_doc that fit in overlap
                    while total_len > self.chunk_overlap and current_doc:
                        popped = current_doc.pop(0)
                        total_len -= len(popped) + (len(separator) if current_doc else 0)

                    # If current_doc became completely empty and overlap is requested, preserve trailing tokens
                    if not current_doc and doc_text and self.chunk_overlap > 0:
                        tail = doc_text[-self.chunk_overlap:].strip()
                        if " " in tail:
                            clean_tail = tail[tail.find(" ") + 1:].strip()
                            if clean_tail:
                                tail = clean_tail
                        if tail:
                            current_doc = [tail]
                            total_len = len(tail)

                if len(s) > self.chunk_size:
                    # Item itself is larger than chunk_size; recurse with finer separator
                    if new_separators:
                        sub_chunks = self._recursive_split(s, new_separators)
                        final_chunks.extend(sub_chunks)
                    else:
                        # Hard character boundary split as last resort
                        for start in range(0, len(s), self.chunk_size - self.chunk_overlap):
                            end = min(start + self.chunk_size, len(s))
                            chunk_part = s[start:end].strip()
                            if chunk_part:
                                final_chunks.append(chunk_part)
                            if end == len(s):
                                break
                    current_doc = []
                    total_len = 0
                else:
                    while current_doc and (
                        total_len + (len(separator) if current_doc else 0) + len(s) > self.chunk_size
                    ):
                        popped = current_doc.pop(0)
                        total_len -= len(popped) + (len(separator) if current_doc else 0)

                    if current_doc:
                        current_doc.append(s)
                        total_len += len(separator) + len(s)
                    else:
                        current_doc = [s]
                        total_len = len(s)
            else:
                current_doc.append(s)
                total_len += s_len

        if current_doc:
            doc_text = separator.join(current_doc).strip()
            if doc_text and (not final_chunks or final_chunks[-1] != doc_text):
                final_chunks.append(doc_text)

        return final_chunks


class DocumentChunker:
    """
    Coordinates chunking of parsed Documents into traceable, deterministic TextChunks.
    Respects page boundaries for PDFs and generates unique deterministic IDs.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitter = RecursiveTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    @staticmethod
    def compute_sha256(text: str) -> str:
        """Deterministic SHA-256 of chunk text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def chunk_document(self, document: Document) -> List[TextChunk]:
        """
        Split a document into deterministic chunks.
        For multi-page PDFs, chunks are scoped per-page to retain accurate page attribution.
        """
        chunks: List[TextChunk] = []
        global_chunk_idx = 0

        # Multi-page documents (PDFs with discrete pages)
        if document.pages and len(document.pages) > 1:
            for page in document.pages:
                if not page.text.strip():
                    continue

                page_splits = self.splitter.split_text(page.text)
                for page_local_idx, text_part in enumerate(page_splits):
                    chunk_hash = self.compute_sha256(text_part)
                    chunk_id = (
                        f"{document.document_id}_p{page.page_number}_c{page_local_idx:04d}"
                    )
                    chunk = TextChunk(
                        chunk_id=chunk_id,
                        document_id=document.document_id,
                        chunk_index=global_chunk_idx,
                        text=text_part,
                        category=document.category,
                        source=document.source,
                        page_number=page.page_number,
                        content_hash=chunk_hash,
                        metadata={
                            **document.metadata,
                            "filename": document.filename,
                            "document_type": document.document_type,
                            "page_number": page.page_number,
                            "total_pages": document.total_pages,
                        },
                    )
                    chunks.append(chunk)
                    global_chunk_idx += 1
        else:
            # Single-page documents (TXT, Markdown, or single-page PDF)
            page_num = document.pages[0].page_number if document.pages else None
            splits = self.splitter.split_text(document.content)

            for idx, text_part in enumerate(splits):
                chunk_hash = self.compute_sha256(text_part)
                if page_num is not None and document.document_type == "pdf":
                    chunk_id = f"{document.document_id}_p{page_num}_c{idx:04d}"
                else:
                    chunk_id = f"{document.document_id}_c{idx:04d}"

                chunk = TextChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    chunk_index=global_chunk_idx,
                    text=text_part,
                    category=document.category,
                    source=document.source,
                    page_number=page_num,
                    content_hash=chunk_hash,
                    metadata={
                        **document.metadata,
                        "filename": document.filename,
                        "document_type": document.document_type,
                        "page_number": page_num,
                        "total_pages": document.total_pages,
                    },
                )
                chunks.append(chunk)
                global_chunk_idx += 1

        return chunks

    def chunk_batch(self, documents: List[Document]) -> List[TextChunk]:
        """Chunk a batch of documents sequentially."""
        all_chunks: List[TextChunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
