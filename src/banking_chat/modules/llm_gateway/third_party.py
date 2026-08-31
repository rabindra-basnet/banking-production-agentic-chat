"""Third-party commercial LLM client (OpenAI GPT-4o)."""

from __future__ import annotations

from typing import Any

import httpx

from banking_chat.core.config.settings import get_settings


class ThirdPartyLLMClient:
    """Client for querying external commercial model APIs."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.llm_openai_api_key
        self.base_url = base_url or settings.llm_openai_base_url
        self.model = model or settings.llm_openai_model
        self.temperature = settings.llm_openai_temperature
        self.max_tokens = settings.llm_openai_max_tokens

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send chat completion request to third-party OpenAI-compatible endpoint."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        if not self.api_key:
            # Fallback mock for testing when API key is empty
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "Response generated via third-party cloud model mock.",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 120, "completion_tokens": 45, "total_tokens": 165},
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data: dict[str, Any] = resp.json()
                    return data
        except Exception:
            pass

        return {
            "choices": [{"message": {"role": "assistant", "content": "Service temporarily unavailable."}}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
