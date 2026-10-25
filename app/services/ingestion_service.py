"""Ingestion Service coordinating document loading, validation, chunking, and duplicate management."""

from pathlib import Path
from typing import Dict, List, Any, Optional
from app.ingestion.loader import DocumentLoader, Document
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
