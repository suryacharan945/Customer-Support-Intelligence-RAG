"""API Router aggregation."""

from fastapi import APIRouter
from app.api.endpoints import health, rag, feedback, analytics

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(rag.router)
api_router.include_router(feedback.router)
api_router.include_router(analytics.router)
