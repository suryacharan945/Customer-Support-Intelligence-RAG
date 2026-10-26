"""Embedding Provider Architecture supporting Local, Remote (Colab/API), and Mock implementations.

Conforms to sentence-transformers/all-MiniLM-L6-v2 specification:
- Output Dimension: 384
- Distance Metric: Cosine
- Vector Normalization: L2 Norm = 1.0
"""

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List, Optional
import httpx

from app.core.config import settings
from app.core.logging import logger


class EmbeddingError(Exception):
    """Base exception for embedding operations."""
    pass


class EmbeddingConfigurationError(EmbeddingError):
    """Raised when embedding provider configuration is invalid or unpermitted."""
    pass


class EmbeddingConnectionError(EmbeddingError):
    """Raised when connecting to remote embedding provider fails."""
    pass


class EmbeddingTimeoutError(EmbeddingError):
    """Raised when remote embedding provider times out."""
    pass


class MockEmbeddingForbiddenError(EmbeddingError):
    """Raised when mock embeddings are requested outside explicitly enabled test mode."""
    pass


class BaseEmbeddingProvider(ABC):
    """Abstract base class for all embedding providers."""

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        dimension: int = settings.EMBEDDING_DIMENSION,
        distance_metric: str = settings.EMBEDDING_DISTANCE_METRIC,
    ):
        self.model_name = model_name
        self.dimension = dimension
        self.distance_metric = distance_metric

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a single query text."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of document chunks."""
        pass


class SentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """
    Local embedding generator using sentence-transformers.
    Protected by strict storage policy: only loaded when explicitly permitted.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        device: str = settings.EMBEDDING_DEVICE,
        allow_local: Optional[bool] = None,
    ):
        super().__init__(model_name=model_name)
        self.device = device
        self.allow_local = (
            allow_local if allow_local is not None else settings.ALLOW_LOCAL_EMBEDDINGS
        )
        self._model = None
        self._init_model()

    def _init_model(self):
        if not self.allow_local:
            raise EmbeddingConfigurationError(
                "Local embedding execution is disabled under current storage policy. "
                "Use RemoteEmbeddingProvider or set ALLOW_LOCAL_EMBEDDINGS=True with explicit approval."
            )
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local embedding model: {self.model_name} on {self.device}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
        except ImportError as e:
            raise EmbeddingConfigurationError(
                f"sentence-transformers library not installed locally: {e}"
            ) from e
        except Exception as e:
            raise EmbeddingError(f"Failed to initialize local embedding model: {e}") from e

    def embed_query(self, text: str) -> List[float]:
        if not self._model:
            raise EmbeddingConfigurationError("Local embedding model is uninitialized.")
        vector = self._model.encode(text, normalize_embeddings=True, convert_to_numpy=True)
        return vector.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not self._model:
            raise EmbeddingConfigurationError("Local embedding model is uninitialized.")
        if not texts:
            return []
        vectors = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return vectors.tolist()


class RemoteEmbeddingProvider(BaseEmbeddingProvider):
    """
    Remote embedding generator communicating via HTTP with Google Colab or cloud API.
    Guarantees 0 GB local model weight storage on the developer machine.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        timeout_seconds: float = 10.0,
    ):
        super().__init__(model_name=model_name)
        if endpoint_url is not None:
            self.endpoint_url = endpoint_url
        else:
            self.endpoint_url = settings.REMOTE_EMBEDDING_ENDPOINT
        self.timeout_seconds = timeout_seconds

        if not self.endpoint_url:
            raise EmbeddingConfigurationError(
                "Remote embedding endpoint URL is not configured. "
                "Set REMOTE_EMBEDDING_ENDPOINT or launch Colab inference tunnel."
            )

    def embed_query(self, text: str) -> List[float]:
        results = self.embed_documents([text])
        if not results:
            raise EmbeddingError("Remote embedding provider returned empty results for query.")
        return results[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        payload = {
            "input": texts,
            "model": self.model_name,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(self.endpoint_url, json=payload)
                if response.status_code != 200:
                    raise EmbeddingError(
                        f"Remote embedding provider returned HTTP {response.status_code}: {response.text}"
                    )
                data = response.json()

                # Handle OpenAI / TEI standard response: {"data": [{"embedding": [...]}, ...]}
                if "data" in data and isinstance(data["data"], list):
                    return [item["embedding"] for item in data["data"]]

                # Handle flat list: {"embeddings": [[...], ...]}
                if "embeddings" in data and isinstance(data["embeddings"], list):
                    return data["embeddings"]

                # Handle direct array response: [[...], ...]
                if isinstance(data, list):
                    return data

                raise EmbeddingError(f"Unexpected response schema from remote embedding endpoint: {data}")
        except httpx.ConnectError as e:
            raise EmbeddingConnectionError(
                f"Failed to connect to remote embedding endpoint at {self.endpoint_url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise EmbeddingTimeoutError(
                f"Remote embedding endpoint at {self.endpoint_url} timed out after {self.timeout_seconds}s: {e}"
            ) from e
        except EmbeddingError:
            raise
        except Exception as e:
            raise EmbeddingError(f"Unexpected remote embedding error: {e}") from e


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic pseudo-embedding provider strictly for automated unit tests.
    Derives normalized 384-dimensional unit vectors from SHA-256 hash seeds.
    Never permitted in production or normal development execution.
    """

    def __init__(
        self,
        model_name: str = settings.EMBEDDING_MODEL_NAME,
        dimension: int = settings.EMBEDDING_DIMENSION,
        allow_mock: Optional[bool] = None,
    ):
        super().__init__(model_name=model_name, dimension=dimension)
        self.allow_mock = (
            allow_mock
            if allow_mock is not None
            else (settings.ALLOW_MOCK_FALLBACK or settings.TEST_MODE)
        )
        if not self.allow_mock:
            raise MockEmbeddingForbiddenError(
                "MockEmbeddingProvider requested but mock fallback is disabled. "
                "Mock embeddings are prohibited in non-test modes."
            )

    def _generate_vector(self, text: str) -> List[float]:
        """Generate a deterministic 384-dimensional L2-normalized vector from text."""
        # Base seed from SHA-256
        seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        vector: List[float] = []

        # Expand seed deterministically to requested dimension (384)
        for i in range(self.dimension):
            # Mix hash byte with index
            b = seed_bytes[i % len(seed_bytes)]
            val = math.sin((b + i * 13) * 0.17)
            vector.append(val)

        # L2-normalize vector to unit length (norm = 1.0) for cosine distance
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_query(self, text: str) -> List[float]:
        return self._generate_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


def get_embedding_provider(
    provider_type: Optional[str] = None,
    allow_mock: Optional[bool] = None,
    allow_local: Optional[bool] = None,
    endpoint_url: Optional[str] = None,
) -> BaseEmbeddingProvider:
    """
    Factory function resolving configured embedding provider.
    Defaults to settings.EMBEDDING_PROVIDER.
    """
    ptype = (provider_type or settings.EMBEDDING_PROVIDER).lower()

    if ptype == "mock":
        return MockEmbeddingProvider(allow_mock=allow_mock)
    elif ptype == "local":
        return SentenceTransformerEmbeddingProvider(allow_local=allow_local)
    elif ptype in ("remote", "colab"):
        return RemoteEmbeddingProvider(endpoint_url=endpoint_url)
    else:
        raise EmbeddingConfigurationError(
            f"Unsupported embedding provider: '{ptype}'. Choose from 'remote', 'local', or 'mock'."
        )
