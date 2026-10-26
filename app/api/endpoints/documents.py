"""Document Lifecycle Management API endpoints.

Handles document upload, format validation, path traversal defense,
content validation, lifecycle tracking (6 states), searchability gating,
and atomic document deletion across manifest, storage, and vector store.
"""

import os
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.deps import (
    get_ingestion_service,
    get_manifest,
    get_vector_retriever,
    get_bm25_retriever,
)
from app.services.ingestion_service import IngestionService
from app.ingestion.manifest import IngestionManifest
from app.retrieval.vector_store import VectorStoreRetriever
from app.retrieval.bm25 import BM25Retriever
from app.ingestion.loader import (
    UnsupportedFileTypeError,
    OversizedFileError,
    CorruptedFileError,
    EmptyDocumentError,
    PathTraversalError,
)

router = APIRouter(prefix="/documents", tags=["Document Lifecycle Management"])


class DocumentSummary(BaseModel):
    document_id: str
    filename: str
    category: str
    document_type: str
    lifecycle_status: str = Field(..., description="One of: uploaded, processed, pending_index, indexed, indexing_failed, deleted")
    is_searchable: bool = Field(..., description="True ONLY when lifecycle_status == 'indexed'")
    chunk_count: int
    file_size_bytes: int
    version: int
    first_ingested: str
    last_seen: str


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentSummary]


class DocumentUploadResponse(BaseModel):
    status: str
    document_id: str
    filename: str
    category: str
    lifecycle_status: str
    is_searchable: bool
    chunk_count: int
    file_size_bytes: int
    content_hash: str
    message: str


class DocumentDeleteResponse(BaseModel):
    status: str
    message: str
    document_id: str
    deleted_chunks: int = 0


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest Knowledge Base Document",
)
@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Ingest Knowledge Base Document (Alias)",
)
async def upload_document(
    file: UploadFile = File(..., description="Document file (.pdf, .txt, or .md)"),
    category: str = Form("product_manual", description="Category: product_manual, troubleshooting, warranty, faq"),
    ingestion: IngestionService = Depends(get_ingestion_service),
    vector_retriever: VectorStoreRetriever = Depends(get_vector_retriever),
):
    """
    Upload and preprocess a document into the customer support knowledge base.
    
    Enforces:
    - Path traversal protection (directory traversal sequences are rejected)
    - 10MB maximum file size limit (HTTP 413)
    - File format restriction (.pdf, .txt, .md) (HTTP 400)
    - Content validation (%PDF- signature, valid UTF-8 text) (HTTP 400)
    - Duplicate detection (idempotent, skips redundant re-chunking)
    - Document lifecycle tracking (uploaded -> processed -> pending_index -> indexed)
    - Searchability gating: document is NEVER searchable until indexed
    """
    raw_filename = file.filename or "unnamed_document.txt"

    # Explicit Path Traversal Defense
    if ".." in raw_filename or "/" in raw_filename or "\\" in raw_filename:
        # Check if it attempts directory traversal
        base = os.path.basename(raw_filename).strip()
        if not base or ".." in base:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid filename '{raw_filename}': Path traversal sequences are strictly prohibited.",
            )

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read uploaded file stream: {e}",
        )

    try:
        res = ingestion.process_uploaded_file(
            filename=raw_filename,
            content=content,
            category=category,
            vector_retriever=vector_retriever,
        )
    except OversizedFileError as e:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum upload size (10MB): {e}",
        )
    except (UnsupportedFileTypeError, PathTraversalError, EmptyDocumentError, CorruptedFileError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation failed for uploaded file '{raw_filename}': {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion processing error: {e}",
        )

    return DocumentUploadResponse(
        status=res.get("status", "SUCCESS"),
        document_id=res["document_id"],
        filename=res["filename"],
        category=res["category"],
        lifecycle_status=res.get("lifecycle_status", "pending_index"),
        is_searchable=res.get("is_searchable", False),
        chunk_count=res.get("chunk_count", 0),
        file_size_bytes=res.get("file_size_bytes", len(content)),
        content_hash=res.get("content_hash", ""),
        message=res.get("message", "Document processed successfully"),
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List Knowledge Base Documents",
)
async def list_documents(
    category: Optional[str] = Query(None, description="Filter by category (product_manual, troubleshooting, warranty, faq)"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by lifecycle status (uploaded, processed, pending_index, indexed, indexing_failed, deleted)"),
    include_deleted: bool = Query(False, description="Include soft-deleted documents"),
    manifest: IngestionManifest = Depends(get_manifest),
):
    """
    List registered documents from the ingestion manifest.
    Tracks lifecycle states and searchability boundaries.
    """
    raw_docs = manifest.list_documents(
        category=category,
        include_deleted=include_deleted,
        status=status_filter,
    )

    docs = []
    for d in raw_docs:
        docs.append(
            DocumentSummary(
                document_id=d.get("document_id", ""),
                filename=d.get("filename", ""),
                category=d.get("category", "general"),
                document_type=d.get("document_type", "txt"),
                lifecycle_status=d.get("lifecycle_status", "indexed"),
                is_searchable=d.get("is_searchable", False),
                chunk_count=d.get("chunk_count", 0),
                file_size_bytes=d.get("file_size_bytes", 0),
                version=d.get("version", 1),
                first_ingested=d.get("first_ingested", ""),
                last_seen=d.get("last_seen", ""),
            )
        )

    return DocumentListResponse(total=len(docs), documents=docs)


@router.get(
    "/{document_id}",
    response_model=DocumentSummary,
    summary="Get Document Details by ID",
)
async def get_document(
    document_id: str,
    manifest: IngestionManifest = Depends(get_manifest),
):
    """Retrieve details for a single document by its document_id."""
    doc = manifest.get_document_by_id(document_id)
    if not doc or doc.get("status") == "DELETED" or doc.get("lifecycle_status") == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found or has been deleted.",
        )

    return DocumentSummary(
        document_id=doc.get("document_id", ""),
        filename=doc.get("filename", ""),
        category=doc.get("category", "general"),
        document_type=doc.get("document_type", "txt"),
        lifecycle_status=doc.get("lifecycle_status", "indexed"),
        is_searchable=doc.get("is_searchable", False),
        chunk_count=doc.get("chunk_count", 0),
        file_size_bytes=doc.get("file_size_bytes", 0),
        version=doc.get("version", 1),
        first_ingested=doc.get("first_ingested", ""),
        last_seen=doc.get("last_seen", ""),
    )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Atomically Delete Document",
)
async def delete_document(
    document_id: str,
    ingestion: IngestionService = Depends(get_ingestion_service),
    vector_retriever: VectorStoreRetriever = Depends(get_vector_retriever),
    bm25_retriever: BM25Retriever = Depends(get_bm25_retriever),
):
    """
    Atomically delete a document across all project storage layers:
    1. Removes chunks from ChromaDB vector collection.
    2. Removes chunks from BM25 sparse keyword index.
    3. Deletes raw source file from storage.
    4. Marks record as 'deleted' in the persistent ingestion manifest.
    
    Safe and returns HTTP 404 if the document is not found or already deleted.
    """
    res = ingestion.delete_document(
        document_id=document_id,
        vector_retriever=vector_retriever,
        bm25_retriever=bm25_retriever,
    )

    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res.get("message", f"Document '{document_id}' not found or already deleted."),
        )

    return DocumentDeleteResponse(
        status="success",
        message=res.get("message", f"Document '{document_id}' successfully deleted."),
        document_id=document_id,
        deleted_chunks=res.get("deleted_chunks", 0),
    )
