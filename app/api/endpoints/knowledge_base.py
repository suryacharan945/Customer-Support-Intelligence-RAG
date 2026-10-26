"""Knowledge Base Status and Diagnostic Endpoints."""

import os
import shutil
from typing import Dict, Any
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_settings, get_manifest, get_vector_retriever
from app.core.config import Settings
from app.ingestion.manifest import IngestionManifest
from app.retrieval.vector_store import VectorStoreRetriever

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base & Indexing Status"])


class KnowledgeBaseStatusResponse(BaseModel):
    status: str = "operational"
    total_active_documents: int
    total_active_chunks: int
    searchable_documents_count: int
    documents_by_category: Dict[str, int]
    documents_by_lifecycle_status: Dict[str, int]
    vector_store: Dict[str, Any]
    storage: Dict[str, Any]


@router.get(
    "/status",
    response_model=KnowledgeBaseStatusResponse,
    summary="Get Comprehensive Knowledge Base Status",
)
async def get_knowledge_base_status(
    app_settings: Settings = Depends(get_settings),
    manifest: IngestionManifest = Depends(get_manifest),
    vector_retriever: VectorStoreRetriever = Depends(get_vector_retriever),
):
    """
    Retrieve comprehensive knowledge-base telemetry:
    - Breakdown of documents across categories
    - Breakdown across the 6 lifecycle states
    - Searchability count
    - ChromaDB collection metrics
    - Cloud storage (Google Drive) sync and local disk budget status
    """
    summary = manifest.get_status_summary()
    gdrive_connected = os.path.isdir(app_settings.GOOGLE_DRIVE_ROOT)
    total, used, free = shutil.disk_usage("C:\\")

    vector_count = 0
    if vector_retriever and vector_retriever._collection:
        vector_count = vector_retriever.count()

    return KnowledgeBaseStatusResponse(
        status="operational",
        total_active_documents=summary["total_documents"],
        total_active_chunks=summary["total_active_chunks"],
        searchable_documents_count=summary["searchable_documents_count"],
        documents_by_category=summary["by_category"],
        documents_by_lifecycle_status=summary["by_lifecycle_status"],
        vector_store={
            "collection_name": vector_retriever.collection_name if vector_retriever else None,
            "total_indexed_chunks": vector_count,
            "is_connected": bool(vector_retriever and vector_retriever._collection is not None),
        },
        storage={
            "google_drive_connected": gdrive_connected,
            "google_drive_root": app_settings.GOOGLE_DRIVE_ROOT,
            "local_free_disk_gb": round(free / (1024**3), 2),
            "storage_budget_mb": app_settings.LOCAL_MAX_STORAGE_BUDGET_MB,
        },
    )
