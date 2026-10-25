"""Automated test suite verifying error handling, mock elimination, citation integrity, and provider routing."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from starlette.testclient import TestClient
from app.main import app
from app.retrieval.base import BaseRetriever, RetrievalResult
from app.retrieval.vector_store import (
    VectorStoreRetriever,
    VectorStoreNotInitializedError,
    VectorStoreQueryError,
)
from app.generation.llm_client import (
    LLMClient,
    ProviderNotImplementedError,
    ProviderNotConfiguredError,
    RemoteInferenceError,
    RemoteInferenceTimeoutError,
    LLMError,
)
from app.services.rag_service import RAGService

client = TestClient(app)


# --------------------------------------------------------------------------
# 1. Missing Vector Database Tests
# --------------------------------------------------------------------------

def test_missing_vector_db_raises_uninitialized_error():
    """Verify that uninitialized ChromaDB raises an error and does not silently mock."""
    retriever = VectorStoreRetriever(allow_mock=False)
    retriever._client = None
    retriever._collection = None

    with pytest.raises(VectorStoreNotInitializedError) as exc_info:
        retriever.retrieve("test query")
    assert "Vector database is uninitialized" in str(exc_info.value)


def test_api_returns_503_when_vector_db_uninitialized():
    """Verify that the API returns HTTP 503 when vector DB is unavailable and mock is disabled."""
    with patch("app.services.rag_service.rag_service.vector_retriever.retrieve") as mock_retrieve:
        mock_retrieve.side_effect = VectorStoreNotInitializedError("Database not connected")
        response = client.post("/api/v1/rag/query", json={"query": "How to reset?"})
        assert response.status_code == 503
        assert "Vector store unavailable" in response.json()["detail"]


# --------------------------------------------------------------------------
# 2. Empty Retrieval & No-Evidence Tests
# --------------------------------------------------------------------------

def test_empty_retrieval_returns_evidence_insufficient_response():
    """Verify that empty retrieval returns an honest, un-hallucinated response with no citations or fabricated confidence."""
    async def _test():
        class EmptyRetriever(BaseRetriever):
            def retrieve(self, query: str, top_k: int = 5):
                return []

        service = RAGService(vector_retriever=EmptyRetriever(), allow_mock=False)
        response = await service.process_query("What is the warranty policy for device X?")

        assert response.evidence_found is False
        assert len(response.citations) == 0
        assert response.contexts_used == 0
        assert response.retrieval_similarity is None
        assert response.confidence_score is None  # Absolutely no fabricated confidence
        assert response.requires_human_clarification is True
        assert "could not find sufficient information" in response.answer.lower()
        assert response.is_mock is False

    asyncio.run(_test())


# --------------------------------------------------------------------------
# 3. Retrieval Failure Tests
# --------------------------------------------------------------------------

def test_retrieval_failure_raises_vector_store_query_error():
    """Verify that database query exceptions raise VectorStoreQueryError."""
    retriever = VectorStoreRetriever(allow_mock=False)
    retriever._client = MagicMock()
    retriever._collection = MagicMock()
    retriever._collection.query.side_effect = RuntimeError("Disk I/O error in SQLite")

    with pytest.raises(VectorStoreQueryError) as exc_info:
        retriever.retrieve("test query")
    assert "query execution failed" in str(exc_info.value)


# --------------------------------------------------------------------------
# 4. LLM Provider Routing & Unimplemented Provider Tests
# --------------------------------------------------------------------------

def test_groq_without_key_raises_not_configured():
    """Verify that selecting Groq without API key raises ProviderNotConfiguredError."""
    async def _test():
        client_llm = LLMClient(provider="groq", allow_mock=False)
        with patch("app.core.config.settings.GROQ_API_KEY", ""):
            with pytest.raises(ProviderNotConfiguredError):
                await client_llm.generate_response("system", "user")

    asyncio.run(_test())


def test_groq_with_key_raises_not_implemented():
    """Verify that selecting Groq stub raises ProviderNotImplementedError."""
    async def _test():
        client_llm = LLMClient(provider="groq", allow_mock=False)
        with patch("app.core.config.settings.GROQ_API_KEY", "dummy_key"):
            with pytest.raises(ProviderNotImplementedError) as exc:
                await client_llm.generate_response("system", "user")
            assert "stub" in str(exc.value).lower()

    asyncio.run(_test())


def test_gemini_without_key_raises_not_configured():
    """Verify that selecting Gemini without API key raises ProviderNotConfiguredError."""
    async def _test():
        client_llm = LLMClient(provider="gemini", allow_mock=False)
        with patch("app.core.config.settings.GEMINI_API_KEY", ""):
            with pytest.raises(ProviderNotConfiguredError):
                await client_llm.generate_response("system", "user")

    asyncio.run(_test())


def test_ollama_not_configured_raises_error():
    """Verify that Ollama raises ProviderNotConfiguredError until configured."""
    async def _test():
        client_llm = LLMClient(provider="ollama", allow_mock=False)
        with pytest.raises(ProviderNotConfiguredError):
            await client_llm.generate_response("system", "user")

    asyncio.run(_test())


def test_unknown_provider_raises_value_error():
    """Verify that an unknown provider string raises ValueError."""
    async def _test():
        client_llm = LLMClient(provider="unsupported_provider", allow_mock=False)
        with pytest.raises(ValueError) as exc:
            await client_llm.generate_response("system", "user")
        assert "Unsupported LLM provider" in str(exc.value)

    asyncio.run(_test())


# --------------------------------------------------------------------------
# 5. Remote LLM Timeout & Failure Handling
# --------------------------------------------------------------------------

def test_colab_timeout_raises_remote_timeout_error():
    """Verify that Colab request timeout raises RemoteInferenceTimeoutError."""
    async def _test():
        import httpx
        client_llm = LLMClient(provider="colab_remote", allow_mock=False)

        with patch("httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Read timed out")):
            with pytest.raises(RemoteInferenceTimeoutError):
                await client_llm.generate_response("system", "user")

    asyncio.run(_test())


def test_colab_connection_error_raises_remote_inference_error():
    """Verify that Colab unreachable host raises RemoteInferenceError without silent fallback."""
    async def _test():
        import httpx
        client_llm = LLMClient(provider="colab_remote", allow_mock=False)

        with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
            with pytest.raises(RemoteInferenceError) as exc:
                await client_llm.generate_response("system", "user")
            assert "Could not connect to Colab" in str(exc.value)

    asyncio.run(_test())


# --------------------------------------------------------------------------
# 6. Explicit Mock Mode Tests
# --------------------------------------------------------------------------

def test_explicit_mock_mode_behavior():
    """Verify that mock mode is only executed when explicitly enabled and flags is_mock=True."""
    async def _test():
        retriever = VectorStoreRetriever(allow_mock=True)
        results = retriever.retrieve("printer reset")
        assert len(results) > 0
        assert results[0].metadata.get("is_mock") is True

        llm = LLMClient(provider="mock", allow_mock=True)
        res = await llm.generate_response("system", "user")
        assert res["is_mock"] is True
        assert "[MOCK RESPONSE]" in res["text"]

    asyncio.run(_test())


def test_mock_provider_fails_if_mock_disabled():
    """Verify that mock provider fails if allow_mock=False and TEST_MODE=False."""
    async def _test():
        llm = LLMClient(provider="mock", allow_mock=False)
        with patch("app.core.config.settings.TEST_MODE", False):
            with pytest.raises(LLMError):
                await llm.generate_response("system", "user")

    asyncio.run(_test())


# --------------------------------------------------------------------------
# 7. Conservative Citation & Evidence Integrity Tests
# --------------------------------------------------------------------------

def test_conservative_citations_match_retrieved_evidence():
    """Verify that citations match exact retrieved sources with uncalibrated similarity."""
    async def _test():
        class MockEvidenceRetriever(BaseRetriever):
            def retrieve(self, query: str, top_k: int = 5):
                return [
                    RetrievalResult(
                        document_id="doc_01",
                        text="Disconnect the power cable and hold the reset switch for 5 seconds.",
                        score=0.88,
                        source="hardware_manual.pdf",
                        metadata={"section": "power_cycle", "is_mock": False},
                    ),
                    RetrievalResult(
                        document_id="doc_02",
                        text="Factory reset clears network credentials.",
                        score=0.74,
                        source="network_faq.md",
                        metadata={"section": "security", "is_mock": False},
                    ),
                ]

        class FakeLLM(LLMClient):
            async def generate_response(self, system_prompt: str, user_prompt: str):
                return {"text": "Step 1: Disconnect power. Step 2: Hold reset.", "is_mock": False}

        service = RAGService(
            vector_retriever=MockEvidenceRetriever(),
            llm_client=FakeLLM(),
            allow_mock=False,
        )

        response = await service.process_query("How to reset?")

        assert response.evidence_found is True
        assert len(response.citations) == 2
        assert response.citations[0].document_source == "hardware_manual.pdf"
        assert response.citations[0].page_or_section == "power_cycle"
        # Citation score reflects the hybrid retrieval fused score
        assert response.citations[0].relevance_score > 0.0
        assert response.citations[1].document_source == "network_faq.md"
        assert response.citations[1].page_or_section == "security"
        assert response.retrieval_similarity == round(
            (response.citations[0].relevance_score + response.citations[1].relevance_score) / 2, 4
        )
        assert response.confidence_score is None  # Uncalibrated confidence not fabricated
        assert response.is_mock is False

    asyncio.run(_test())
