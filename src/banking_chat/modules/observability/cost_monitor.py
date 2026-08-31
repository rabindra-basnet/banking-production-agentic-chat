"""Cost monitoring and budget threshold alerting."""

from __future__ import annotations

import logging

from banking_chat.core.config.settings import get_settings

logger = logging.getLogger("banking_chat.cost_monitor")


class CostMonitor:
    """Monitors running expenditure against daily and monthly budgets."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def check_budget_thresholds(self, total_daily_cost: float) -> bool:
        """Check if daily consumption has crossed warning or critical thresholds."""
        daily_budget = self.settings.cost_daily_budget_usd
        ratio = total_daily_cost / daily_budget if daily_budget > 0 else 0.0

        if ratio >= 1.0:
            logger.error(
                "CRITICAL: Daily LLM budget exceeded! Spent: $%.2f / Limit: $%.2f",
                total_daily_cost,
                daily_budget,
            )
            return False
        if ratio >= 0.8:
            logger.warning(
                "WARNING: 80%% of daily LLM budget reached. Spent: $%.2f / Limit: $%.2f",
                total_daily_cost,
                daily_budget,
            )

        return True
