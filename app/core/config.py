"""Core Configuration Management for the RAG + MCP Capstone Platform."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable override and safe defaults."""

    # Application
    PROJECT_NAME: str = "Multi-Context Intelligent RAG System"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"

    # Persistent Storage Paths (Google Drive First Policy)
    GOOGLE_DRIVE_ROOT: str = r"G:\My Drive\Internship_RAG_MCP_Capstone"
    LOCAL_EPHEMERAL_CHROMA_DIR: str = ".chroma_live"
    LOCAL_MAX_STORAGE_BUDGET_MB: int = 1024

    # LLM & Remote Compute
    # Supported providers: colab_remote, groq, gemini, ollama, mock
    LLM_PROVIDER: str = "colab_remote"
    COLAB_API_ENDPOINT: str = "http://localhost:8001/v1"
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OLLAMA_API_ENDPOINT: str = "http://localhost:11434/v1"
    DEFAULT_MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.3"

    # Testing & Mock Configuration (Strictly disabled in normal dev / production)
    ALLOW_MOCK_FALLBACK: bool = False
    TEST_MODE: bool = False

    # Embedding Settings
    # Supported providers: remote, local, mock
    EMBEDDING_PROVIDER: str = "remote"
    ALLOW_LOCAL_EMBEDDINGS: bool = False
    REMOTE_EMBEDDING_ENDPOINT: str = "http://localhost:8001/v1/embeddings"
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_MODEL_REVISION: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int = 384
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_DISTANCE_METRIC: str = "cosine"

    # Retrieval Settings
    CHROMA_COLLECTION_NAME: str = "apexprint_knowledge_base"
    TOP_K_RETRIEVAL: int = 5
    HYBRID_SEARCH_ALPHA: float = 0.6
    BM25_ENABLED: bool = True

    # Active Learning & Feedback
    CONFIDENCE_THRESHOLD_CLARIFY: float = 0.65
    HUMAN_FEEDBACK_AUTO_ARCHIVE: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
