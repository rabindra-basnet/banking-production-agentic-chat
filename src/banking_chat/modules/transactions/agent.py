"""Transactions Agent implementation handling transaction query workflows."""

from __future__ import annotations

from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.core.common.utils import format_currency
from banking_chat.modules.transactions.prompts import TRANSACTION_AGENT_SYSTEM_PROMPT
from banking_chat.modules.transactions.schemas import TransactionQueryRequest
from banking_chat.modules.transactions.service import TransactionsService


class TransactionsAgent:
    """Specialized agent for transaction inquiries and analytics."""

    def __init__(self, service: TransactionsService | None = None) -> None:
        self.service = service or TransactionsService()
        self.system_prompt = TRANSACTION_AGENT_SYSTEM_PROMPT

    async def run(self, user_message: str, user: AuthenticatedUser, **kwargs: Any) -> str:
        """Process a transactions domain user query."""
        lower = user_message.lower()
        if "spending" in lower or "summary" in lower or "breakdown" in lower:
            summary = await self.service.get_spending_summary(user.customer_id, days=30)
            spent = format_currency(summary.total_spent)
            received = format_currency(summary.total_received)
            return (
                f"**30-Day Spending Summary:**\n"
                f"- Total Debits (Spent): {spent}\n"
                f"- Total Credits (Received): {received}\n"
                f"- Net Cash Flow: {format_currency(summary.net_flow)}"
            )

        limit = 5
        query = TransactionQueryRequest(limit=limit)
        if "credit" in lower or "salary" in lower or "received" in lower:
            query.transaction_type = "credit"
        elif "debit" in lower or "spent" in lower:
            query.transaction_type = "debit"

        result = await self.service.get_transactions(user.customer_id, query)
        if not result.transactions:
            return "No transactions found matching your request."

        lines = [f"Here are your latest {len(result.transactions)} transactions:"]
        for t in result.transactions:
            dt_str = t.date.strftime("%d %b %Y, %I:%M %p")
            sign = "+" if t.type == "credit" else "-"
            amt = format_currency(t.amount)
            lines.append(f"- **{dt_str}**: {t.description} | `{sign}{amt}` [{t.channel}]")

        return "\n".join(lines)
