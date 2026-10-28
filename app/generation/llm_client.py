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

    def __init__(
        self,
        provider: Optional[str] = None,
        allow_mock: Optional[bool] = None,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: Optional[float] = None,
        allow_fallback: Optional[bool] = None,
    ):
        self.provider = (provider or settings.LLM_PROVIDER).lower()
        self.endpoint = (endpoint or settings.COLAB_API_ENDPOINT).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.COLAB_API_KEY
        self.model_name = model_name or settings.DEFAULT_MODEL_NAME
        self.allow_mock = allow_mock if allow_mock is not None else settings.ALLOW_MOCK_FALLBACK
        self.timeout = timeout or settings.REMOTE_INFERENCE_TIMEOUT
        if allow_fallback is not None:
            self.allow_fallback = allow_fallback
        elif self.provider == "colab_remote":
            # Strict colab_remote provider does not silently fall back unless explicitly requested
            self.allow_fallback = False
        else:
            self.allow_fallback = getattr(settings, "ALLOW_LOCAL_FALLBACK", True) and self.allow_mock is not False

        # Auto-detect from colab_endpoint.json if no explicit endpoint/key was passed
        if self.provider in ("colab_remote", "auto") and endpoint is None and not self.api_key:
            from pathlib import Path
            for candidate in [Path("colab_endpoint.json"), Path(settings.GOOGLE_DRIVE_ROOT) / "colab_endpoint.json"]:
                if candidate.exists():
                    try:
                        with open(candidate, "r", encoding="utf-8") as f:
                            cfg = json.load(f)
                            if cfg.get("endpoint"):
                                self.endpoint = cfg["endpoint"].rstrip("/")
                            if cfg.get("token"):
                                self.api_key = cfg["token"]
                        break
                    except Exception:
                        pass

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route generation request to the configured backend.
        Never silently falls back to synthetic mock text unless provider='mock' or allow_mock=True.
        Supports intelligent local grounded synthesis when Colab is offline.
        """
        active_provider = (provider or self.provider).lower()
        logger.info(f"Generating response using provider: '{active_provider}' (Model: {self.model_name})")

        from app.generation.local_synthesizer import local_synthesizer

        if active_provider == "colab_remote":
            try:
                return await self._call_colab_endpoint(system_prompt, user_prompt)
            except (RemoteInferenceError, RemoteInferenceTimeoutError) as exc:
                if self.allow_fallback:
                    logger.warning(
                        f"Colab endpoint unreachable ({exc}). Falling back to local grounded knowledge base synthesis."
                    )
                    return local_synthesizer.synthesize(user_prompt, is_fallback=True)
                raise
        elif active_provider in ("local", "offline", "local_grounded"):
            return local_synthesizer.synthesize(user_prompt, is_fallback=False)
        elif active_provider == "auto":
            try:
                return await self._call_colab_endpoint(system_prompt, user_prompt)
            except Exception as exc:
                logger.info(f"Auto-provider: Colab unavailable ({exc}), engaging local grounded synthesis.")
                return local_synthesizer.synthesize(user_prompt, is_fallback=True)
        elif active_provider == "groq":
            return await self._call_groq_api(system_prompt, user_prompt)
        elif active_provider == "gemini":
            return await self._call_gemini_api(system_prompt, user_prompt)
        elif active_provider == "ollama":
            return await self._call_ollama_api(system_prompt, user_prompt)
        elif active_provider == "mock":
            if not self.allow_mock and not settings.TEST_MODE:
                raise LLMError("Mock LLM provider invoked while mock mode is disabled in settings.")
            return self._mock_generation(user_prompt)
        else:
            raise ValueError(
                f"Unsupported LLM provider: '{active_provider}'. "
                f"Configured options: ['colab_remote', 'local', 'auto', 'groq', 'gemini', 'ollama', 'mock']."
            )

    async def _call_colab_endpoint(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Send payload to remote Google Colab GPU server with authentication and bounded limits."""
        import time
        import httpx

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": settings.MAX_GENERATION_TOKENS,
        }

        try:
            t0 = time.perf_counter()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(
                    f"{self.endpoint}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                latency_ms = round((time.perf_counter() - t0) * 1000, 2)

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if not choices:
                            raise RemoteInferenceError(f"Colab returned empty choices list: {data}")
                        answer = choices[0].get("message", {}).get("content", "")
                        return {
                            "text": answer,
                            "model": data.get("model", self.model_name),
                            "provider": "colab_remote",
                            "is_mock": False,
                            "latency_ms": latency_ms,
                            "usage": data.get("usage", {}),
                        }
                    except Exception as exc:
                        if isinstance(exc, RemoteInferenceError):
                            raise
                        raise RemoteInferenceError(f"Malformed JSON from Colab inference endpoint: {resp.text}") from exc
                elif resp.status_code == 401:
                    raise RemoteInferenceError(
                        "Authentication failed (HTTP 401) against Colab endpoint. Ensure COLAB_API_KEY is configured correctly."
                    )
                else:
                    raise RemoteInferenceError(
                        f"Colab inference endpoint returned HTTP {resp.status_code}: {resp.text}"
                    )
        except httpx.TimeoutException as exc:
            t_str = f"{int(self.timeout)}s" if self.timeout == int(self.timeout) else f"{self.timeout}s"
            raise RemoteInferenceTimeoutError(
                f"Colab inference endpoint timed out after {t_str} at {self.endpoint}"
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
