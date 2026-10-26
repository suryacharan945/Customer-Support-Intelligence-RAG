"""Test suite for Embedding Providers: dimensionality, normalization, mock isolation, and remote error handling."""

import math
from unittest.mock import patch, MagicMock
import httpx
import pytest

from app.retrieval.embeddings import (
    BaseEmbeddingProvider,
    SentenceTransformerEmbeddingProvider,
    RemoteEmbeddingProvider,
    MockEmbeddingProvider,
    EmbeddingError,
    EmbeddingConfigurationError,
    EmbeddingConnectionError,
    EmbeddingTimeoutError,
    MockEmbeddingForbiddenError,
    get_embedding_provider,
)
from app.core.config import settings


def test_embedding_dimensionality():
    """1. Test that embedding vectors have exact dimensionality of 384 and unit norm."""
    provider = MockEmbeddingProvider(allow_mock=True)
    vec = provider.embed_query("ApexPrint ProX-400 laser printer")

    assert len(vec) == 384
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-4


def test_embedding_determinism():
    """Test that identical input strings produce byte-for-byte identical embedding vectors."""
    provider = MockEmbeddingProvider(allow_mock=True)
    text = "Error E-101 Paper Jam clearing procedure"

    vec1 = provider.embed_query(text)
    vec2 = provider.embed_query(text)
    vec3 = provider.embed_query("Different text content entirely")

    assert vec1 == vec2
    assert vec1 != vec3

    # Batch embedding consistency
    batch_vecs = provider.embed_documents([text, "Different text content entirely"])
    assert len(batch_vecs) == 2
    assert batch_vecs[0] == vec1
    assert batch_vecs[1] == vec3


def test_model_configuration_consistency():
    """2. Test model name, revision, dimension, and distance metric consistency with settings."""
    assert settings.EMBEDDING_MODEL_NAME == "sentence-transformers/all-MiniLM-L6-v2"
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.EMBEDDING_DISTANCE_METRIC == "cosine"

    provider = MockEmbeddingProvider(allow_mock=True)
    assert provider.model_name == settings.EMBEDDING_MODEL_NAME
    assert provider.dimension == settings.EMBEDDING_DIMENSION
    assert provider.distance_metric == settings.EMBEDDING_DISTANCE_METRIC


def test_mock_isolation_forbidden():
    """13. Test that mock embeddings cannot be instantiated when mock mode is disabled."""
    with pytest.raises(MockEmbeddingForbiddenError):
        MockEmbeddingProvider(allow_mock=False)


def test_local_embedding_disabled_without_explicit_permission():
    """Test that local embedding model execution is refused when allow_local is False."""
    with pytest.raises(EmbeddingConfigurationError) as exc_info:
        SentenceTransformerEmbeddingProvider(allow_local=False)
    assert "Local embedding execution is disabled" in str(exc_info.value)


def test_remote_embedding_unconfigured_error():
    """18a. Test that RemoteEmbeddingProvider raises error when endpoint URL is empty."""
    with pytest.raises(EmbeddingConfigurationError):
        RemoteEmbeddingProvider(endpoint_url="")


def test_remote_embedding_connection_error():
    """18b. Test that connecting to an unreachable remote endpoint raises EmbeddingConnectionError."""
    provider = RemoteEmbeddingProvider(
        endpoint_url="http://127.0.0.1:59999/v1/embeddings",
        timeout_seconds=1.0,
    )
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(EmbeddingConnectionError):
            provider.embed_query("Test query")


def test_remote_embedding_timeout_error():
    """18c. Test that a remote timeout raises EmbeddingTimeoutError."""
    provider = RemoteEmbeddingProvider(
        endpoint_url="http://localhost:8001/v1/embeddings",
        timeout_seconds=0.001,
    )
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Read timed out")):
        with pytest.raises(EmbeddingTimeoutError):
            provider.embed_query("Test query")


def test_remote_embedding_successful_parsing():
    """Test parsing standard TEI / OpenAI embedding payload from remote provider."""
    provider = RemoteEmbeddingProvider(endpoint_url="http://mock-colab-endpoint/v1/embeddings")
    mock_vector = [0.05] * 384

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "data": [{"embedding": mock_vector}],
        "model": "sentence-transformers/all-MiniLM-L6-v2",
    }

    with patch("httpx.Client.post", return_value=mock_resp):
        res = provider.embed_query("Sample text")
        assert len(res) == 384
        assert res == mock_vector


def test_embedding_factory_resolution():
    """Test get_embedding_provider factory with various configurations."""
    mock_p = get_embedding_provider("mock", allow_mock=True)
    assert isinstance(mock_p, MockEmbeddingProvider)

    with pytest.raises(EmbeddingConfigurationError):
        get_embedding_provider("unsupported_provider_type")
