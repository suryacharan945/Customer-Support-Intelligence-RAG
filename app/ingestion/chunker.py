"""Context-preserving document chunker for multi-source knowledge synthesis."""

from typing import List, Dict, Any
from app.ingestion.loader import Document


class TextChunk:
    """Represents a chunked passage with traceable metadata."""
    def __init__(self, text: str, chunk_index: int, metadata: Dict[str, Any]):
        self.text = text
        self.chunk_index = chunk_index
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "chunk_index": self.chunk_index,
            "metadata": self.metadata,
        }


class DocumentChunker:
    """Splits documents into overlapping chunks for semantic retrieval."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, document: Document) -> List[TextChunk]:
        """Split a single document into overlapping character chunks."""
        text = document.content
        chunks = []
        if not text.strip():
            return chunks

        start = 0
        chunk_idx = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk_str = text[start:end].strip()

            if chunk_str:
                chunk_meta = document.metadata.copy()
                chunk_meta["chunk_id"] = f"{document.metadata.get('source')}_{chunk_idx}"
                chunks.append(TextChunk(text=chunk_str, chunk_index=chunk_idx, metadata=chunk_meta))
                chunk_idx += 1

            if end == text_len:
                break
            start += self.chunk_size - self.chunk_overlap

        return chunks

    def chunk_batch(self, documents: List[Document]) -> List[TextChunk]:
        """Process a collection of documents."""
        all_chunks = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
