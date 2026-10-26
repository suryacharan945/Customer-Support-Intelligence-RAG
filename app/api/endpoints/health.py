"""Health and readiness diagnostic endpoints."""

import os
import shutil
import time
from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from app.core.config import settings, Settings
from app.api.deps import get_settings, get_vector_retriever, get_manifest
from app.retrieval.vector_store import VectorStoreRetriever
from app.ingestion.manifest import IngestionManifest

router = APIRouter(tags=["Health & Status"])

START_TIME = time.time()


@router.get("/health", summary="System Health Check")
async def health_check(app_settings: Settings = Depends(get_settings)):
    """Verify application availability, storage connection, and uptime."""
    gdrive_connected = os.path.isdir(app_settings.GOOGLE_DRIVE_ROOT)
    total, used, free = shutil.disk_usage("C:\\")

    return {
        "status": "healthy",
        "app_name": app_settings.PROJECT_NAME,
        "version": app_settings.VERSION,
        "environment": app_settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "storage": {
            "google_drive_connected": gdrive_connected,
            "google_drive_root": app_settings.GOOGLE_DRIVE_ROOT,
            "local_free_disk_gb": round(free / (1024**3), 2),
            "storage_budget_mb": app_settings.LOCAL_MAX_STORAGE_BUDGET_MB,
        },
        "compute": {
            "llm_provider": app_settings.LLM_PROVIDER,
            "model_name": app_settings.DEFAULT_MODEL_NAME,
        },
    }


@router.get("/ready", summary="Deep Readiness Probe")
async def readiness_probe(
    app_settings: Settings = Depends(get_settings),
    vector_retriever: VectorStoreRetriever = Depends(get_vector_retriever),
    manifest: IngestionManifest = Depends(get_manifest),
):
    """
    Perform deep readiness check across all critical subsystems:
    storage, manifest, vector database, embedding provider, and LLM configuration.
    Returns HTTP 200 if fully operational; returns HTTP 503 if any subsystem is unready.
    """
    # 1. Storage check (Google Drive or fallback local storage writable)
    gdrive_connected = os.path.isdir(app_settings.GOOGLE_DRIVE_ROOT)
    storage_ready = gdrive_connected or os.path.exists("tmp")

    # 2. Manifest check
    manifest_ready = manifest is not None and isinstance(manifest.manifest_data, dict)

    # 3. Vector Store check
    vector_ready = False
    if vector_retriever:
        if vector_retriever._collection is not None:
            vector_ready = True
        elif vector_retriever.allow_mock or app_settings.ALLOW_MOCK_FALLBACK:
            vector_ready = True

    # 4. Embedding provider check
    embedding_ready = bool(
        app_settings.EMBEDDING_PROVIDER
        or (vector_retriever and vector_retriever.embedding_provider is not None)
    )

    # 5. LLM provider check
    llm_ready = bool(
        app_settings.LLM_PROVIDER in ("colab_remote", "groq", "gemini", "ollama", "mock")
        or app_settings.ALLOW_MOCK_FALLBACK
    )

    all_ready = (
        storage_ready
        and manifest_ready
        and vector_ready
        and embedding_ready
        and llm_ready
    )

    content = {
        "status": "ready" if all_ready else "not_ready",
        "ready": all_ready,
        "checks": {
            "storage": storage_ready,
            "manifest": manifest_ready,
            "vector_store": vector_ready,
            "embedding_provider": embedding_ready,
            "llm_provider": llm_ready,
        },
        "details": {
            "google_drive_connected": gdrive_connected,
            "vector_store_collection": vector_retriever.collection_name if vector_retriever else None,
            "indexed_chunks_count": vector_retriever.count() if vector_retriever and vector_retriever._collection else 0,
            "llm_provider": app_settings.LLM_PROVIDER,
            "environment": app_settings.ENVIRONMENT,
        },
    }

    if not all_ready:
        return JSONResponse(status_code=503, content=content)

    return content
