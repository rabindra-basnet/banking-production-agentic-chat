"""Context-Aware Coordinator Agent orchestrating multi-agent routing using conversation history and semantic intent."""

from __future__ import annotations

import re
from typing import Any

from banking_chat.core.common.types import AgentName, AuthenticatedUser


class CoordinatorAgent:
    """Classifies user intent and routes to specialized domain agents using context memory, urgency rules, and domain heuristics."""

    ROUTING_DOMAINS: dict[AgentName, dict[str, Any]] = {
        AgentName.SERVICE: {
            "description": "Urgent card blocking, cheque books, KYC updates, dispute raising, account freeze/unfreeze",
            "urgent_indicators": ["lost", "stolen", "block", "fraud", "scam", "unauthorized", "freeze", "compromised"],
            "keywords": [
                "block", "card", "debit card", "credit card", "cheque", "chequebook", "checkbook", "check book",
                "stolen", "lost", "kyc", "citizenship", "nid", "rastriya parichayapatra", "address",
                "dispute", "ticket", "issue", "service", "complaint", "unfreeze", "reissue", "pin reset"
            ],
        },
        AgentName.TRANSACTION: {
            "description": "Fund transfers, Fonepay QR, ConnectIPS, mini-statements, transaction logs, debits & credits",
            "keywords": [
                "transaction", "transactions", "statement", "history", "debit", "credit", "spent", "spending",
                "transfer", "transfers", "fonepay", "connectips", "esewa", "khalti", "npi", "atm", "qr",
                "charge", "charges", "payment", "payments", "paid", "send money", "receive", "remittance",
                "upi", "neft", "rtgs", "imps"
            ],
        },
        AgentName.ACCOUNTS: {
            "description": "Account balances, interest rates, Muddati Khata (Fixed Deposits), account details and branch lookup",
            "keywords": [
                "balance", "balances", "account", "accounts", "saving", "savings", "current", "fd",
                "fixed deposit", "muddati", "muddati khata", "rd", "recurring deposit", "branch",
                "holding", "holdings", "summary", "npr", "rupee", "rupees", "interest rate", "cif"
            ],
        },
    }

    def route_query(
        self,
        query: str,
        user: AuthenticatedUser,
        history: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> AgentName:
        """Analyze query, conversation context memory, and user profile to accurately route to domain agents."""
        text = query.lower().strip()

        # 1. High Priority: Check for critical safety / emergency banking service events
        for indicator in self.ROUTING_DOMAINS[AgentName.SERVICE]["urgent_indicators"]:
            if re.search(rf"\b{re.escape(indicator)}\b", text):
                return AgentName.SERVICE

        # 2. Context Continuity: Check recent conversation turn if query is short / conversational follow-up
        recent_agent: AgentName | None = None
        if history:
            for past_msg in reversed(history[-4:]):
                past_agent_str = past_msg.get("agent") or past_msg.get("metadata", {}).get("agent")
                if past_agent_str:
                    try:
                        recent_agent = AgentName(past_agent_str)
                        break
                    except ValueError:
                        pass

        # 3. Calculate semantic scoring across domain categories
        scores: dict[AgentName, int] = {
            AgentName.SERVICE: 0,
            AgentName.TRANSACTION: 0,
            AgentName.ACCOUNTS: 0,
        }

        for agent_name, domain_data in self.ROUTING_DOMAINS.items():
            for kw in domain_data["keywords"]:
                if re.search(rf"\b{re.escape(kw)}", text):
                    scores[agent_name] += 2

        # 4. If query is ambiguous / follow-up, give weight to the ongoing context memory agent
        if recent_agent and scores[recent_agent] == max(scores.values()):
            scores[recent_agent] += 1

        best_agent = max(scores, key=lambda a: scores[a])
        if scores[best_agent] > 0:
            return best_agent

        # 5. Follow-up context fallback if no direct keyword matched
        if recent_agent:
            return recent_agent

        # Default fallback
        return AgentName.ACCOUNTS
