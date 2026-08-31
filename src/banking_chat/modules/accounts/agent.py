"""Accounts Agent implementation handling account information workflows."""

from __future__ import annotations

from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.core.common.utils import format_currency
from banking_chat.modules.accounts.prompts import ACCOUNTS_AGENT_SYSTEM_PROMPT
from banking_chat.modules.accounts.service import AccountsService


class AccountsAgent:
    """Specialized agent for bank account balances and details."""

    def __init__(self, service: AccountsService | None = None) -> None:
        self.service = service or AccountsService()
        self.system_prompt = ACCOUNTS_AGENT_SYSTEM_PROMPT

    async def run(self, user_message: str, user: AuthenticatedUser, **kwargs: Any) -> str:
        """Process an accounts domain user query."""
        # Simple intent routing / response generation
        lower_msg = user_message.lower()
        if "summary" in lower_msg or "total" in lower_msg or "all" in lower_msg:
            summary = await self.service.get_account_summary(user.customer_id)
            formatted = format_currency(summary.total_balance_inr)
            return (
                f"You have {summary.account_count} account(s) with a total net balance of "
                f"{formatted}. Status: {summary.status}."
            )

        # Default to checking balances
        acc_list = await self.service.get_accounts_by_customer(user.customer_id)
        if not acc_list.accounts:
            return "No active accounts found for your customer ID."

        lines = [f"Here are your account details, {user.name}:"]
        for acc in acc_list.accounts:
            bal = format_currency(acc.balance, acc.currency)
            lines.append(f"- **{acc.account_type.title()} Account** ({acc.account_number}): {bal} [{acc.status}]")

        return "\n".join(lines)
