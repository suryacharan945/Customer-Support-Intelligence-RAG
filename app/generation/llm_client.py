"""LLM Client Adapter with strict error handling, remote execution, and explicit mock isolation."""

import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMError(Exception):
    """Base exception for LLM operations."""
    pass


class ProviderNotImplementedError(LLMError):
    """Raised when an LLM provider is a stub or not yet implemented."""
    pass


class ProviderNotConfiguredError(LLMError):
    """Raised when an LLM provider lacks mandatory credentials or endpoints."""
    pass


class RemoteInferenceError(LLMError):
    """Raised when a remote inference backend fails or returns an error."""
    pass


class RemoteInferenceTimeoutError(RemoteInferenceError):
    """Raised when a remote inference backend times out."""
    pass


class LLMClient:
    """
    Unified client interface for generative model inference.
    Strictly prohibits silent fallbacks to fabricated mock outputs in normal modes.
    """

    def __init__(self, provider: Optional[str] = None, allow_mock: Optional[bool] = None):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.endpoint = settings.COLAB_API_ENDPOINT
        self.model_name = settings.DEFAULT_MODEL_NAME
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK

    async def generate_response(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        Route generation request to the configured backend.
        Never silently falls back to synthetic mock text unless provider='mock' or allow_mock=True.
        """
        logger.info(f"Generating response using provider: '{self.provider}' (Model: {self.model_name})")

        if self.provider == "colab_remote":
            return await self._call_colab_endpoint(system_prompt, user_prompt)
        elif self.provider == "groq":
            return await self._call_groq_api(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return await self._call_gemini_api(system_prompt, user_prompt)
        elif self.provider == "ollama":
            return await self._call_ollama_api(system_prompt, user_prompt)
        elif self.provider == "mock":
            if not self.allow_mock and not settings.TEST_MODE:
                raise LLMError("Mock LLM provider invoked while mock mode is disabled in settings.")
            return self._mock_generation(user_prompt)
        else:
            raise ValueError(
                f"Unsupported LLM provider: '{self.provider}'. "
                f"Configured options: ['colab_remote', 'groq', 'gemini', 'ollama', 'mock']."
            )

    async def _call_colab_endpoint(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Send payload to remote Google Colab GPU server."""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.2,
                }
                resp = await client.post(f"{self.endpoint}/chat/completions", json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    answer = data["choices"][0]["message"]["content"]
                    return {
                        "text": answer,
                        "model": self.model_name,
                        "provider": "colab_remote",
                        "is_mock": False,
                    }
                else:
                    raise RemoteInferenceError(
                        f"Colab inference endpoint returned HTTP {resp.status_code}: {resp.text}"
                    )
        except httpx.TimeoutException as exc:
            raise RemoteInferenceTimeoutError(
                f"Colab inference endpoint timed out after 30s at {self.endpoint}"
            ) from exc
        except httpx.ConnectError as exc:
            raise RemoteInferenceError(
                f"Could not connect to Colab inference endpoint at {self.endpoint}. "
                f"Ensure the remote server or tunnel is running."
            ) from exc
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise
            raise RemoteInferenceError(f"Unexpected error communicating with Colab: {exc}") from exc

    async def _call_groq_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Groq Cloud API (marked as stub/not implemented)."""
        if not settings.GROQ_API_KEY:
            raise ProviderNotConfiguredError("Groq provider requested but GROQ_API_KEY is not set.")
        raise ProviderNotImplementedError(
            "Groq provider integration is currently a stub and not yet integration-tested."
        )

    async def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API (marked as stub/not implemented)."""
        if not settings.GEMINI_API_KEY:
            raise ProviderNotConfiguredError("Gemini provider requested but GEMINI_API_KEY is not set.")
        raise ProviderNotImplementedError(
            "Gemini provider integration is currently a stub and not yet integration-tested."
        )

    async def _call_ollama_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Ollama inference endpoint (target architecture, not yet configured)."""
        raise ProviderNotConfiguredError(
            f"Ollama inference endpoint is not configured at {settings.OLLAMA_API_ENDPOINT}."
        )

    def _mock_generation(self, user_prompt: str) -> Dict[str, Any]:
        """Explicit mock response generator reserved strictly for test suites."""
        return {
            "text": (
                "[MOCK RESPONSE] Based on the test documentation, hold the power button for 10 "
                "seconds to reset your device. (Generated under explicit test mode)."
            ),
            "model": "mock-test-engine",
            "provider": "mock",
            "is_mock": True,
        }
