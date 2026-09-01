"""Hybrid LLM Router selecting between self-hosted and commercial cloud LLMs."""

from __future__ import annotations

import logging

from banking_chat.core.common.exceptions import PIILeakageError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.modules.llm_gateway.cost_tracker import CostTracker
from banking_chat.modules.llm_gateway.self_hosted import SelfHostedLLMClient
from banking_chat.modules.llm_gateway.third_party import ThirdPartyLLMClient
from banking_chat.modules.pii_guard.detector import PIIDetector

llm_logger = logging.getLogger("banking_chat.modules.llm_gateway")


class LLMRouter:
    """Intelligently routes prompts to self-hosted or cloud LLMs based on security and tier."""

    def __init__(
        self,
        self_hosted: SelfHostedLLMClient | None = None,
        third_party: ThirdPartyLLMClient | None = None,
        detector: PIIDetector | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self.self_hosted = self_hosted or SelfHostedLLMClient()
        self.third_party = third_party or ThirdPartyLLMClient()
        self.detector = detector or PIIDetector()
        self.cost_tracker = cost_tracker or CostTracker()

    async def route_and_generate(
        self,
        messages: list[dict[str, str]],
        user: AuthenticatedUser,
        prefer_cloud: bool = False,
    ) -> tuple[str, float]:
        """Route to appropriate model, execute generation, track cost, and return content + cost."""
        # Step 1: Scan for unmasked PII
        combined_text = " ".join(m.get("content", "") for m in messages)
        pii_result = self.detector.detect(combined_text)

        llm_logger.info(
            "[LLM_GATEWAY] customer=%s | Incoming prompt messages=%d | PII detected=%s",
            user.customer_id, len(messages), pii_result.has_pii,
        )
        for idx, msg in enumerate(messages):
            llm_logger.info("[LLM_GATEWAY] message[%d] role=%s | content=%s", idx, msg.get("role"), msg.get("content"))

        # Step 2: Routing policy
        # If PII is detected, MUST use self-hosted on-premise model to prevent cloud data leakage
        if pii_result.has_pii:
            res = await self.self_hosted.generate(messages)
            model = self.self_hosted.model
            cost = self.cost_tracker.record_usage(
                model,
                res.get("usage", {}).get("prompt_tokens", 0),
                res.get("usage", {}).get("completion_tokens", 0),
            )
            content: str = res["choices"][0]["message"]["content"]
            llm_logger.info(
                "[LLM_GATEWAY] customer=%s | Routed to self_hosted model=%s | cost=%.6f | response=%s",
                user.customer_id, model, cost, content,
            )
            return content, cost

        # For privileged/premium users without PII or if cloud requested, use Third-Party
        if prefer_cloud or user.tier in (CustomerTier.PREMIUM, CustomerTier.PRIVILEGED):
            # Double check for PII leakage before sending to third-party
            if pii_result.has_pii:
                raise PIILeakageError(list(pii_result.entity_counts.keys()))

            res = await self.third_party.generate(messages)
            model = self.third_party.model
            cost = self.cost_tracker.record_usage(
                model,
                res.get("usage", {}).get("prompt_tokens", 0),
                res.get("usage", {}).get("completion_tokens", 0),
            )
            content = res["choices"][0]["message"]["content"]
            llm_logger.info(
                "[LLM_GATEWAY] customer=%s | Routed to third_party model=%s | cost=%.6f | response=%s",
                user.customer_id, model, cost, content,
            )
            return content, cost

        # Standard tier or default uses self-hosted
        res = await self.self_hosted.generate(messages)
        model = self.self_hosted.model
        cost = self.cost_tracker.record_usage(
            model,
            res.get("usage", {}).get("prompt_tokens", 0),
            res.get("usage", {}).get("completion_tokens", 0),
        )
        content = res["choices"][0]["message"]["content"]
        llm_logger.info(
            "[LLM_GATEWAY] customer=%s | Routed to self_hosted model=%s | cost=%.6f | response=%s",
            user.customer_id, model, cost, content,
        )
        return content, cost
