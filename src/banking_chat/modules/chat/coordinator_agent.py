"""Coordinator Agent orchestrating multi-agent routing and safety checks."""

from __future__ import annotations

import re
from typing import Any

from banking_chat.core.common.types import AgentName, AuthenticatedUser


class CoordinatorAgent:
    """Classifies user intent and routes to specialized domain agents."""

    ROUTING_KEYWORDS: dict[str, list[str]] = {
        AgentName.ACCOUNTS: [
            "balance",
            "account",
            "saving",
            "current",
            "fd",
            "fixed deposit",
            "ifsc",
            "branch",
            "holding",
            "summary",
        ],
        AgentName.TRANSACTION: [
            "transaction",
            "statement",
            "history",
            "debit",
            "credit",
            "spent",
            "spend",
            "transfer",
            "upi",
            "neft",
            "charge",
            "payment",
            "paid",
        ],
        AgentName.SERVICE: [
            "cheque",
            "checkbook",
            "card block",
            "block card",
            "stolen",
            "lost card",
            "kyc",
            "address change",
            "service request",
            "status",
            "ticket",
        ],
    }

    def route_query(self, query: str, user: AuthenticatedUser, **kwargs: Any) -> AgentName:
        """Analyze query keywords and user context to determine target agent."""
        text = query.lower()

        # Score agents by keyword occurrence
        scores: dict[str, int] = {
            AgentName.ACCOUNTS: 0,
            AgentName.TRANSACTION: 0,
            AgentName.SERVICE: 0,
        }

        for agent, keywords in self.ROUTING_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}\b", text):
                    scores[agent] += 1

        best_agent = max(scores, key=lambda a: scores[a])
        if scores[best_agent] > 0:
            return AgentName(best_agent)

        # Default fallback
        return AgentName.ACCOUNTS
