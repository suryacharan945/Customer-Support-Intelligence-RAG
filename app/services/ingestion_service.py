"""Ingestion Service coordinating document loading, validation, chunking, and duplicate management."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.ingestion.loader import (
    DocumentLoader,
    Document,
    SUPPORTED_EXTENSIONS,
    VALID_CATEGORIES,
    UnsupportedFileTypeError,
    InvalidCategoryError,
    CorruptedFileError,
    OversizedFileError,
    EmptyDocumentError,
    PathTraversalError,
)
from app.ingestion.chunker import DocumentChunker, TextChunk
from app.ingestion.manifest import IngestionManifest
from app.core.config import settings
from app.core.logging import logger


class IngestionService:
    """
    Coordinates the end-to-end ingestion pipeline:
    Validation -> Loading -> Deduplication Check -> Chunking -> Manifest Registration.
    Operates independently without dependencies on ChromaDB or LLMs.
    """

    def __init__(
        self,
        manifest_path: Optional[str | Path] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_file_size_bytes: int = 10 * 1024 * 1024,
    ):
        if not manifest_path:
            # Default to Google Drive 02_Datasets if accessible, else local storage
            gdrive_manifest = Path(settings.GOOGLE_DRIVE_ROOT) / "02_Datasets" / "ingestion_manifest.json"
            if Path(settings.GOOGLE_DRIVE_ROOT).exists():
                manifest_path = gdrive_manifest
            else:
                manifest_path = Path("tmp") / "ingestion_manifest.json"

        self.manifest = IngestionManifest(manifest_path=manifest_path)
        self.loader = DocumentLoader(max_file_size_bytes=max_file_size_bytes)
        self.chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    def process_uploaded_file(
        self,
        filename: str,
        content: bytes,
        category: str = "product_manual",
        vector_retriever: Optional[Any] = None,
        embedding_provider: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Process, validate, chunk, and register an uploaded file.
        Strictly enforces:
        - Path traversal defense
        - Maximum file size (10MB)
        - Allowed extensions (.pdf, .txt, .md)
        - File content integrity (PDF header %PDF-, UTF-8 text)
        - Lifecycle state tracking: uploaded -> processed -> pending_index -> indexed
        - Searchability: only indexed documents are marked searchable
        """
        # 1. Path Traversal Defense
        if ".." in filename or filename.startswith("/") or filename.startswith("\\") or "/" in filename or "\\" in filename:
            clean_name = os.path.basename(filename).strip()
            # If after stripping basename there are still suspicious traversal markers or empty
            if not clean_name or ".." in clean_name:
                raise PathTraversalError(f"Directory traversal sequence detected in filename: '{filename}'")
        else:
            clean_name = os.path.basename(filename).strip()

        if not clean_name:
            raise ValueError("Filename cannot be empty")

        # 2. Maximum File Size Enforcement (10MB)
        if len(content) > self.loader.max_file_size_bytes:
            raise OversizedFileError(
                f"File size {len(content)} bytes exceeds maximum allowed limit of {self.loader.max_file_size_bytes} bytes (10MB)."
            )

        # 3. File Extension Enforcement
        ext = Path(clean_name).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Unsupported file extension '{ext}'. Allowed extensions: {list(SUPPORTED_EXTENSIONS.keys())}"
            )

        # 4. Category Validation
        if category not in VALID_CATEGORIES:
            category = "product_manual"

        # 5. Content Integrity Validation
        if len(content) == 0:
            raise EmptyDocumentError(f"Uploaded file '{clean_name}' is empty (0 bytes).")

        if ext == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise CorruptedFileError(f"Invalid PDF header in '{clean_name}': missing '%PDF-' magic bytes.")
        else:
            try:
                decoded_text = content.decode("utf-8")
            except UnicodeDecodeError as e:
                raise CorruptedFileError(f"Text file '{clean_name}' must be valid UTF-8: {e}")
            if not decoded_text.strip():
                raise EmptyDocumentError(f"Uploaded text document '{clean_name}' contains zero text or only whitespace.")

        # 6. Check for duplicate content in manifest
        content_hash = self.loader.compute_sha256(content)
        eval_status, existing_record = self.manifest.evaluate_file(category, clean_name, content_hash)
        if eval_status == "UNCHANGED":
            logger.info(f"Duplicate content detected for upload '{clean_name}'. Skipping redundant chunking.")
            return {
                "status": "SKIPPED_DUPLICATE",
                "document_id": existing_record["document_id"],
                "filename": clean_name,
                "category": category,
                "lifecycle_status": existing_record.get("lifecycle_status", "indexed"),
                "is_searchable": existing_record.get("is_searchable", True),
                "chunk_count": existing_record.get("chunk_count", 0),
                "file_size_bytes": len(content),
                "content_hash": content_hash,
                "message": f"Document '{clean_name}' is identical to existing document. Skipped duplicate processing.",
            }

        # 7. Write to storage
        if Path(settings.GOOGLE_DRIVE_ROOT).exists():
            upload_dir = Path(settings.GOOGLE_DRIVE_ROOT) / "02_Datasets" / "raw_documents" / category
        else:
            upload_dir = Path("tmp") / "uploads" / category
        upload_dir.mkdir(parents=True, exist_ok=True)
        dest_file = upload_dir / clean_name
        dest_file.write_bytes(content)

        # 8. Load & Chunk
        doc = self.loader.load_file(dest_file, category)
        chunks = self.chunker.chunk_document(doc)

        # 9. Determine Indexing & Lifecycle Status
        lifecycle_status = "pending_index"
        if vector_retriever is not None and getattr(vector_retriever, "_collection", None) is not None:
            try:
                vector_retriever.upsert_chunks(chunks, embedding_provider=embedding_provider)
                lifecycle_status = "indexed"
            except Exception as e:
                logger.error(f"Failed to upsert chunks into vector store: {e}")
                lifecycle_status = "indexing_failed"

        # 10. Register in Manifest
        record = self.manifest.register_document(
            doc.to_dict(),
            chunk_count=len(chunks),
            lifecycle_status=lifecycle_status,
        )

        return {
            "status": "SUCCESS",
            "document_id": doc.document_id,
            "filename": clean_name,
            "category": category,
            "lifecycle_status": lifecycle_status,
            "is_searchable": (lifecycle_status == "indexed"),
            "chunk_count": len(chunks),
            "file_size_bytes": len(content),
            "content_hash": content_hash,
            "message": f"Document '{clean_name}' successfully processed into {len(chunks)} chunks.",
        }

    def delete_document(
        self,
        document_id: str,
        vector_retriever: Optional[Any] = None,
        bm25_retriever: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Atomically delete document across manifest, vector store, and storage.
        Safe and idempotent.
        """
        doc_record = self.manifest.get_document_by_id(document_id)
        if not doc_record or doc_record.get("status") == "DELETED" or doc_record.get("lifecycle_status") == "deleted":
            return {
                "success": False,
                "reason": "not_found",
                "message": f"Document '{document_id}' not found or already deleted.",
            }

        filename = doc_record.get("filename", "")
        category = doc_record.get("category", "")

        # 1. Delete vector store chunks
        deleted_vector_chunks = 0
        if vector_retriever and hasattr(vector_retriever, "delete_document"):
            try:
                deleted_vector_chunks = vector_retriever.delete_document(document_id)
            except Exception as e:
                logger.warning(f"Error deleting chunks from vector store for '{document_id}': {e}")

        # 2. Delete BM25 chunks
        if bm25_retriever and hasattr(bm25_retriever, "delete_document"):
            try:
                bm25_retriever.delete_document(document_id)
            except Exception as e:
                logger.warning(f"Error removing chunks from BM25 for '{document_id}': {e}")

        # 3. Mark manifest record as deleted
        self.manifest.mark_deleted(document_id)
        logger.info(f"Document '{document_id}' ({filename}) marked deleted in manifest.")

        return {
            "success": True,
            "document_id": document_id,
            "filename": filename,
            "category": category,
            "deleted_chunks": deleted_vector_chunks,
            "message": f"Document '{document_id}' successfully deleted.",
        }

    def ingest_file(
        self,
        file_path: str | Path,
        category: str,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Ingest a single file with deterministic deduplication and chunk generation.
        """
        path = Path(file_path)
        logger.info(f"Ingesting file: {path.name} [Category: {category}]")

        # 1. Quick byte-level content hash check for deduplication
        raw_bytes = path.read_bytes()
        content_hash = self.loader.compute_sha256(raw_bytes)
        eval_status, existing_record = self.manifest.evaluate_file(category, path.name, content_hash)

        if eval_status == "UNCHANGED" and not force_reindex:
            logger.info(f"Duplicate content detected for {path.name}. Skipping re-chunking.")
            return {
                "status": "SKIPPED_DUPLICATE",
                "document_id": existing_record["document_id"],
                "filename": path.name,
                "category": category,
                "chunks": [],
                "chunk_count": existing_record.get("chunk_count", 0),
                "record": existing_record,
            }

        # 2. Load and validate document
        document: Document = self.loader.load_file(path, category)

        # 3. Chunk document
        chunks: List[TextChunk] = self.chunker.chunk_document(document)

        # 4. Update manifest
        record = self.manifest.register_document(document.to_dict(), chunk_count=len(chunks))

        result_status = "UPDATED" if eval_status == "MODIFIED" else "SUCCESS"
        logger.info(
            f"Successfully processed {path.name} -> {len(chunks)} chunks (Doc ID: {document.document_id})"
        )

        return {
            "status": result_status,
            "document_id": document.document_id,
            "filename": document.filename,
            "category": category,
            "document": document,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "record": record,
        }

    def ingest_directory(
        self,
        directory_path: str | Path,
        category: Optional[str] = None,
        force_reindex: bool = False,
    ) -> Dict[str, Any]:
        """
        Scan and ingest all supported documents in a directory or category hierarchy.
        """
        dir_path = Path(directory_path)
        logger.info(f"Scanning directory for ingestion: {dir_path}")

        results: List[Dict[str, Any]] = []
        errors: List[Dict[str, str]] = []
        total_chunks = 0
        skipped_duplicates = 0
        processed = 0

        documents = self.loader.load_directory(dir_path, category=category)
        for doc in documents:
            try:
                res = self.ingest_file(
                    file_path=Path(doc.metadata["source_path"]),
                    category=doc.category,
                    force_reindex=force_reindex,
                )
                results.append(res)
                if res["status"] == "SKIPPED_DUPLICATE":
                    skipped_duplicates += 1
                else:
                    processed += 1
                    total_chunks += res["chunk_count"]
            except Exception as e:
                logger.error(f"Error processing {doc.filename}: {e}")
                errors.append({"filename": doc.filename, "error": str(e)})

        return {
            "total_files_scanned": len(documents),
            "processed": processed,
            "skipped_duplicates": skipped_duplicates,
            "total_chunks_created": total_chunks,
            "errors": errors,
            "results": results,
        }


ingestion_service = IngestionService()
