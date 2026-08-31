"""Coordinator Agent orchestrating multi-agent routing and safety checks."""

from __future__ import annotations

import re
from typing import Any

from banking_chat.core.common.types import AgentName, AuthenticatedUser


class CoordinatorAgent:
    """Classifies user intent and routes to specialized domain agents."""

    ROUTING_KEYWORDS: dict[AgentName, list[str]] = {
        AgentName.SERVICE: [
            "block",
            "card",
            "cheque",
            "checkbook",
            "check book",
            "stolen",
            "lost",
            "kyc",
            "address",
            "dispute",
            "ticket",
            "issue",
            "service",
            "complaint",
        ],
        AgentName.TRANSACTION: [
            "transaction",
            "transactions",
            "statement",
            "history",
            "debit",
            "credit",
            "spent",
            "spending",
            "transfer",
            "transfers",
            "upi",
            "neft",
            "rtgs",
            "imps",
            "charge",
            "charges",
            "payment",
            "payments",
            "paid",
        ],
        AgentName.ACCOUNTS: [
            "balance",
            "balances",
            "account",
            "accounts",
            "saving",
            "savings",
            "current",
            "fd",
            "fixed deposit",
            "rd",
            "recurring deposit",
            "ifsc",
            "branch",
            "holding",
            "holdings",
            "summary",
        ],
    }

    def route_query(self, query: str, user: AuthenticatedUser, **kwargs: Any) -> AgentName:
        """Analyze query keywords and user context to determine target agent."""
        text = query.lower()

        scores: dict[AgentName, int] = {
            AgentName.SERVICE: 0,
            AgentName.TRANSACTION: 0,
            AgentName.ACCOUNTS: 0,
        }

        # Check for card blocking / urgent services with highest priority
        if "block" in text or "lost" in text or "stolen" in text or "cheque" in text:
            scores[AgentName.SERVICE] += 5

        for agent, keywords in self.ROUTING_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}", text):
                    scores[agent] += 1

        best_agent = max(scores, key=lambda a: scores[a])
        if scores[best_agent] > 0:
            return best_agent

        # Default fallback
        return AgentName.ACCOUNTS
