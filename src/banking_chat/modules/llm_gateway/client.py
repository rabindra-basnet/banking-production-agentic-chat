"""Unified OpenAI-compatible LLM client with cost tracking and streaming.

Single ``LLMClient`` class for every provider (self-hosted / OpenCode Zen /
vLLM / Ollama / OpenAI). Providers are differentiated by ``name`` and share
one dependency (the ``openai`` sdk), so no separate client implementations or
duplicated HTTP stacks are needed.

Cost rates are resolved at runtime from the ``llm_cost_rates`` table so new
providers/models can be priced without code changes. When no row exists, a
provider-level default is used and every invocation is persisted to
``llm_cost_records`` for audit and budget analytics.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai import AsyncOpenAI
from openai._types import Omit
from openai.types.chat import ChatCompletionMessageParam
from sqlalchemy import select

from banking_chat.core.common.exceptions import CostLimitExceededError
from banking_chat.core.config.settings import get_settings
from banking_chat.core.db.session import get_session_factory
from banking_chat.modules.llm_gateway.models import LLMCostRate, LLMCostRecord
from banking_chat.modules.llm_gateway.types import ProviderName

logger = logging.getLogger("banking_chat.modules.llm_gateway")


class LLMClient:
    """Client for querying any OpenAI-compatible chat completions endpoint."""

    # Per-provider default rates (USD per 1K tokens) used when no DB row exists.
    # Per-model overrides are configured at runtime in the llm_cost_rates table.
    PROVIDER_DEFAULT_RATES: dict[ProviderName, dict[str, float]] = {
        "self_hosted": {"input": 0.0, "output": 0.0},  # On-premise: zero marginal API cost
        "third_party": {"input": 0.002, "output": 0.006},  # Generic commercial rate
    }

    def __init__(
        self,
        name: ProviderName,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> None:
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        kwargs: dict[str, Any] = {
            "base_url": self.base_url.rstrip("/"),
            "timeout": 30.0,
        }
        if self.api_key:
            kwargs["api_key"] = self.api_key
        else:
            # Disable the auth guard so key-less gateways (OpenCode Zen) work
            # without credentials; the Authorization header is explicitly Omit()ed
            # per request so nothing is sent.
            kwargs["api_key"] = ""
            kwargs["_enforce_credentials"] = False
        self.client = AsyncOpenAI(**kwargs)

    @property
    def _request_headers(self) -> dict[str, Any]:
        """Headers passed on every request; omits Authorization when no key is set."""
        if self.api_key:
            return {}
        return {"Authorization": Omit()}

    # ── Factories classified by provider name ──────────────────────────
    @classmethod
    def self_hosted(cls) -> LLMClient:
        """Build the self-hosted / local / OpenCode Zen gateway client."""
        settings = get_settings()
        return cls(
            name="self_hosted",
            base_url=settings.llm_self_hosted_base_url,
            api_key=settings.llm_openai_api_key,
            model=settings.llm_self_hosted_model,
            temperature=settings.llm_self_hosted_temperature,
            max_tokens=settings.llm_self_hosted_max_tokens,
        )

    @classmethod
    def third_party(cls) -> LLMClient:
        """Build the commercial / cloud OpenAI-compatible client."""
        settings = get_settings()
        return cls(
            name="third_party",
            base_url=settings.llm_openai_base_url,
            api_key=settings.llm_openai_api_key,
            model=settings.llm_openai_model,
            temperature=settings.llm_openai_temperature,
            max_tokens=settings.llm_openai_max_tokens,
        )

    # ── Cost tracking (DB-backed rates + persisted records) ────────────
    async def _get_rates(self, model: str) -> dict[str, float]:
        """Resolve token rates for this client's provider/model, falling back to provider default."""
        try:
            factory = get_session_factory()
            async with factory() as session:
                stmt = select(LLMCostRate).where(
                    LLMCostRate.provider == self.name,
                    LLMCostRate.model == model,
                )
                result = await session.execute(stmt)
                rate = result.scalars().first()
                if rate is not None:
                    return {"input": rate.input_rate, "output": rate.output_rate}
        except Exception:
            logger.warning(
                "Could not resolve cost rate from DB for provider=%s model=%s; using provider default",
                self.name,
                model,
            )

        return self.PROVIDER_DEFAULT_RATES.get(self.name, {"input": 0.002, "output": 0.006})

    async def calculate_cost(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        model: str | None = None,
    ) -> float:
        """Calculate the cost in USD for the given token usage on this client's provider."""
        model = model or self.model
        rates = await self._get_rates(model)
        cost = (prompt_tokens / 1000.0 * rates["input"]) + (completion_tokens / 1000.0 * rates["output"])
        return round(cost, 6)

    async def record_usage(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        session_id: str | None = None,
        customer_id: str | None = None,
        model: str | None = None,
    ) -> float:
        """Record usage for this client's provider, enforce limits, and persist an audit row."""
        cost = await self.calculate_cost(prompt_tokens, completion_tokens, model=model)

        settings = get_settings()
        if cost > settings.cost_per_interaction_limit_usd:
            raise CostLimitExceededError(cost, settings.cost_per_interaction_limit_usd)

        try:
            factory = get_session_factory()
            async with factory() as session:
                session.add(
                    LLMCostRecord(
                        session_id=session_id,
                        customer_id=customer_id,
                        provider=self.name,
                        model=model or self.model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=prompt_tokens + completion_tokens,
                        cost_usd=cost,
                    )
                )
                await session.commit()
        except Exception:
            logger.warning(
                "Could not persist cost record for provider=%s model=%s",
                self.name,
                model or self.model,
            )

        return cost

    # ── Generation ─────────────────────────────────────────────────────
    async def generate(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Send a chat completion request and return the raw OpenAI response."""
        logger.info(
            "[LLM_CLIENT] provider=%s model=%s | messages=%d",
            self.name,
            self.model,
            len(messages),
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            extra_headers=self._request_headers,
        )
        logger.info(
            "[LLM_CLIENT] provider=%s model=%s | completion ok | usage=%s",
            self.name,
            self.model,
            response.usage,
        )
        return response.model_dump()

    async def stream_generate(
        self,
        messages: list[ChatCompletionMessageParam],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream the assistant reply content token-by-token from the provider.

        Yields delta strings as they arrive; the full completion is assembled
        by the caller. Usage metadata is not available on streaming chunks, so
        callers that need cost tracking should reconstruct token counts from
        the collected text or rely on the aggregate endpoint.
        """
        logger.info(
            "[LLM_CLIENT] provider=%s model=%s | streaming messages=%d",
            self.name,
            self.model,
            len(messages),
        )
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature if temperature is not None else self.temperature,
            max_tokens=max_tokens if max_tokens is not None else self.max_tokens,
            stream=True,
            extra_headers=self._request_headers,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
