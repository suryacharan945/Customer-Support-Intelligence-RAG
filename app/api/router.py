"""API Router aggregation."""

from fastapi import APIRouter
from app.api.endpoints import health, rag, documents, knowledge_base, feedback, analytics

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(rag.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge_base.router)
api_router.include_router(feedback.router)
api_router.include_router(analytics.router)
