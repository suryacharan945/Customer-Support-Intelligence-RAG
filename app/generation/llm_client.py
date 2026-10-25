"""LLM Client Adapter supporting Google Colab Remote, Cloud APIs, and Local Mocking."""

import json
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging import logger


class LLMClient:
    """Unified client interface for generative model inference."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or settings.LLM_PROVIDER
        self.endpoint = settings.COLAB_API_ENDPOINT
        self.model_name = settings.DEFAULT_MODEL_NAME

    async def generate_response(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Route generation request to the configured backend."""
        logger.info(f"Generating response using provider: {self.provider} (Model: {self.model_name})")

        if self.provider == "colab_remote":
            return await self._call_colab_endpoint(system_prompt, user_prompt)
        elif self.provider == "groq" and settings.GROQ_API_KEY:
            return await self._call_groq_api(system_prompt, user_prompt)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            return await self._call_gemini_api(system_prompt, user_prompt)
        else:
            return self._mock_generation(user_prompt)

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
                    return {"text": answer, "model": self.model_name, "provider": "colab_remote"}
                else:
                    logger.warning(f"Colab endpoint returned HTTP {resp.status_code}. Falling back to mock.")
        except Exception as e:
            logger.warning(f"Failed to connect to Colab endpoint ({e}). Using mock response.")

        return self._mock_generation(user_prompt)

    async def _call_groq_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Groq Cloud API."""
        # Stub for Groq API integration
        return self._mock_generation(user_prompt)

    async def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Call Google Gemini API."""
        # Stub for Gemini API integration
        return self._mock_generation(user_prompt)

    def _mock_generation(self, user_prompt: str) -> Dict[str, Any]:
        """Deterministic mock response for offline and testing mode."""
        return {
            "text": (
                "Based on the troubleshooting guide, you can reset your hardware by holding "
                "the power button for 10 seconds until the indicator flashes. If the error persists, "
                "refer to section 4 of the warranty guidelines for replacement terms."
            ),
            "model": "mock-development-engine",
            "provider": "local_mock",
            "confidence_score": 0.94,
        }
