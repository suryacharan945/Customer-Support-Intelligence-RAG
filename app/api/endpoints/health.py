"""Health and readiness diagnostic endpoints."""

import os
import shutil
import time
from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["Health & Status"])

START_TIME = time.time()


@router.get("/health", summary="System Health Check")
async def health_check():
    """Verify application availability, storage connection, and uptime."""
    gdrive_connected = os.path.isdir(settings.GOOGLE_DRIVE_ROOT)
    total, used, free = shutil.disk_usage("C:\\")

    return {
        "status": "healthy",
        "app_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "storage": {
            "google_drive_connected": gdrive_connected,
            "google_drive_root": settings.GOOGLE_DRIVE_ROOT,
            "local_free_disk_gb": round(free / (1024**3), 2),
            "storage_budget_mb": settings.LOCAL_MAX_STORAGE_BUDGET_MB,
        },
        "compute": {
            "llm_provider": settings.LLM_PROVIDER,
            "model_name": settings.DEFAULT_MODEL_NAME,
        },
    }
