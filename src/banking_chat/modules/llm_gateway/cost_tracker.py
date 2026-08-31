"""LLM cost calculation, usage tracking, and budget enforcement."""

from __future__ import annotations

from banking_chat.core.common.exceptions import CostLimitExceededError
from banking_chat.core.config.settings import get_settings


class CostTracker:
    """Calculates LLM query costs and monitors budget thresholds."""

    # Pricing per 1,000 tokens (approximate USD rates)
    MODEL_RATES: dict[str, dict[str, float]] = {
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "llama3.1:8b": {"input": 0.0, "output": 0.0},  # Self-hosted internal zero marginal API cost
    }

    def __init__(self) -> None:
        self.settings = get_settings()
        self.total_spent_today: float = 0.0

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate the cost in USD for a given token usage."""
        rates = self.MODEL_RATES.get(model, {"input": 0.002, "output": 0.006})
        cost = (prompt_tokens / 1000.0 * rates["input"]) + (completion_tokens / 1000.0 * rates["output"])
        return round(cost, 6)

    def record_usage(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Record usage and enforce hard cost limits per interaction."""
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)
        if cost > self.settings.cost_per_interaction_limit_usd:
            raise CostLimitExceededError(cost, self.settings.cost_per_interaction_limit_usd)

        self.total_spent_today += cost
        return cost
