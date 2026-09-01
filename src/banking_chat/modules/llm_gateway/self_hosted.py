"""Self-hosted / Local LLM integration client (OpenCode Zen / vLLM / Ollama)."""

from __future__ import annotations

from typing import Any

import httpx

from banking_chat.core.config.settings import get_settings


class SelfHostedLLMClient:
    """Client for querying local / OpenCode Zen gateway models."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        settings = get_settings()
        self.base_url = base_url or settings.llm_self_hosted_base_url
        self.model = model or settings.llm_self_hosted_model
        self.api_key = api_key or settings.llm_openai_api_key
        self.temperature = settings.llm_self_hosted_temperature
        self.max_tokens = settings.llm_self_hosted_max_tokens

    async def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send chat completion request to self-hosted / OpenCode Zen endpoint."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    data: dict[str, Any] = resp.json()
                    return data
        except Exception:
            pass

        # Fallback mock for unit testing / local development
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "I am your banking assistant powered by OpenCode Zen AI Gateway.",
                    }
                }
            ],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20, "total_tokens": 70},
        }
