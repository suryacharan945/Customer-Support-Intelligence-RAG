"""FastAPI Dependency Injection Providers.

Provides decoupled, testable access to application singletons,
enabling clean overrides during integration and unit testing.
"""

from typing import TYPE_CHECKING
from app.core.config import settings, Settings

if TYPE_CHECKING:
    from app.ingestion.manifest import IngestionManifest
    from app.retrieval.vector_store import VectorStoreRetriever
    from app.retrieval.bm25 import BM25Retriever
    from app.generation.llm_client import LLMClient
    from app.services.rag_service import RAGService
    from app.services.ingestion_service import IngestionService
    from app.services.feedback_service import FeedbackService


def get_settings() -> Settings:
    """Provide application settings."""
    return settings


def get_rag_service():
    """Provide the main RAG & MCP orchestration service."""
    from app.services.rag_service import rag_service
    return rag_service


def get_vector_retriever():
    """Provide the vector database retriever."""
    from app.services.rag_service import rag_service
    return rag_service.vector_retriever


def get_bm25_retriever():
    """Provide the sparse BM25 keyword retriever."""
    from app.services.rag_service import rag_service
    return rag_service.bm25_retriever


def get_llm_client():
    """Provide the LLM generation client."""
    from app.services.rag_service import rag_service
    return rag_service.llm_client


def get_ingestion_service():
    """Provide the document ingestion service."""
    from app.services.ingestion_service import ingestion_service
    return ingestion_service


def get_manifest():
    """Provide the active document ingestion manifest."""
    from app.services.ingestion_service import ingestion_service
    return ingestion_service.manifest


def get_feedback_service():
    """Provide the continuous learning feedback service."""
    from app.services.feedback_service import feedback_service
    return feedback_service
