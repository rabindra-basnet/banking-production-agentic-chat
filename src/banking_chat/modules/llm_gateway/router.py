"""Hybrid LLM Router selecting between self-hosted and commercial cloud LLMs."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from openai.types.chat import ChatCompletionMessageParam

from banking_chat.core.common.exceptions import PIILeakageError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.modules.llm_gateway.client import LLMClient
from banking_chat.modules.pii_guard.detector import PIIDetector

llm_logger = logging.getLogger("banking_chat.modules.llm_gateway")


def _text_content(msg: ChatCompletionMessageParam) -> str:
    """Extract plain-string content from a chat message, ignoring multimodal parts."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    return ""


class LLMRouter:
    """Intelligently routes prompts to self-hosted or cloud LLMs based on security and tier."""

    def __init__(
        self,
        self_hosted: LLMClient | None = None,
        third_party: LLMClient | None = None,
        detector: PIIDetector | None = None,
    ) -> None:
        self.self_hosted = self_hosted or LLMClient.self_hosted()
        self.third_party = third_party or LLMClient.third_party()
        self.detector = detector or PIIDetector()

    # ── Routing policy ─────────────────────────────────────────────────
    def _select_client(
        self,
        user: AuthenticatedUser,
        prefer_cloud: bool,
        messages_content: str,
    ) -> LLMClient:
        """Pick the provider based on PII presence, tier, and user preference."""
        pii_result = self.detector.detect(messages_content)
        llm_logger.info(
            "[LLM_GATEWAY] customer=%s | PII detected=%s",
            user.customer_id,
            pii_result.has_pii,
        )

        # If PII is detected, MUST use self-hosted on-premise model
        if pii_result.has_pii:
            return self.self_hosted

        # Premium/privileged users or explicit cloud request use third-party
        if prefer_cloud or user.tier in (CustomerTier.PREMIUM, CustomerTier.PRIVILEGED):
            # Double check for PII leakage before sending to third-party
            if pii_result.has_pii:
                raise PIILeakageError(list(pii_result.entity_counts.keys()))
            return self.third_party

        # Standard tier or default uses self-hosted
        return self.self_hosted

    async def _record_cost(
        self,
        client: LLMClient,
        session_id: str | None,
        user: AuthenticatedUser,
        res: dict[str, Any],
    ) -> float:
        """Compute and enforce cost for a completed (non-streamed) response."""
        return await client.record_usage(
            prompt_tokens=res.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=res.get("usage", {}).get("completion_tokens", 0),
            session_id=session_id,
            customer_id=user.customer_id,
        )

    # ── Aggregated generation ──────────────────────────────────────────
    async def route_and_generate(
        self,
        messages: list[ChatCompletionMessageParam],
        user: AuthenticatedUser,
        prefer_cloud: bool = False,
        session_id: str | None = None,
    ) -> tuple[str, float]:
        """Route to appropriate model, generate, track cost, and return content + cost."""
        client = self._select_client(
            user,
            prefer_cloud,
            " ".join(_text_content(m) for m in messages),
        )
        for idx, msg in enumerate(messages):
            llm_logger.info(
                "[LLM_GATEWAY] message[%d] role=%s | content=%s",
                idx,
                msg.get("role"),
                _text_content(msg),
            )

        res = await client.generate(messages)
        cost = await self._record_cost(client, session_id, user, res)
        content = res["choices"][0]["message"]["content"]
        llm_logger.info(
            "[LLM_GATEWAY] customer=%s | Routed to provider=%s model=%s | cost=%.6f | response=%s",
            user.customer_id,
            client.name,
            client.model,
            cost,
            content,
        )
        return content, cost

    # ── Streaming generation ───────────────────────────────────────────
    async def stream_generate(
        self,
        messages: list[ChatCompletionMessageParam],
        user: AuthenticatedUser,
        prefer_cloud: bool = False,
        session_id: str | None = None,
    ) -> AsyncGenerator[tuple[str, bool], None]:
        """Stream tokens from the routed provider.

        Yields ``(delta, is_final)`` tuples. The final ``(content, True)``
        yield carries the full assembled message; cost for the streamed
        interaction is estimated from the assembled text by the caller since
        streaming responses do not include usage metadata.
        """
        client = self._select_client(
            user,
            prefer_cloud,
            " ".join(_text_content(m) for m in messages),
        )
        llm_logger.info(
            "[LLM_GATEWAY] customer=%s | Streaming to provider=%s model=%s",
            user.customer_id,
            client.name,
            client.model,
        )

        parts: list[str] = []
        async for delta in client.stream_generate(messages):
            parts.append(delta)
            yield delta, False

        content = "".join(parts)
        yield content, True
