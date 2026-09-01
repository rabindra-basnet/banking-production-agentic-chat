import logging
from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.core.common.utils import format_currency
from banking_chat.modules.accounts.prompts import ACCOUNTS_AGENT_SYSTEM_PROMPT
from banking_chat.modules.accounts.service import AccountsService
from banking_chat.modules.accounts.tools import AccountsTools

logger = logging.getLogger("banking_chat.modules.accounts")


class AccountsAgent:
    """Specialized agent for bank account balances and details executing through AccountsTools."""

    def __init__(
        self,
        service: AccountsService | None = None,
        tools: AccountsTools | None = None,
    ) -> None:
        self.service = service or AccountsService()
        self.tools = tools or AccountsTools()
        self.system_prompt = ACCOUNTS_AGENT_SYSTEM_PROMPT

    async def run(self, user_message: str, user: AuthenticatedUser, **kwargs: Any) -> str:
        """Process an accounts domain user query using domain tools."""
        logger.info(f"Processing accounts query for customer={user.customer_id}: '{user_message}'")
        lower_msg = user_message.lower()

        # 1. Identity & Capability Questions
        if any(w in lower_msg for w in ["who are you", "what is your name", "what can you do", "help"]):
            return (
                f"Namaste {user.name}! 🙏\n\n"
                f"I am the **NepalBank AI Assistant**, your official retail banking concierge.\n\n"
                f"Here is what I can assist you with:\n"
                f"• 💳 **Accounts & Balances**: Check Savings Khata, Muddati Khata & statements\n"
                f"• 💸 **Payments & Transfers**: Fonepay QR queries, ConnectIPS transfers & spending history\n"
                f"• 📋 **Banking Services**: Request Cheque Books (25/50/100 leaves), emergency card blocking & KYC updates\n\n"
                f"How may I help you today?"
            )

        # 2. Summary / Total Balance Tool Call
        if "summary" in lower_msg or "total" in lower_msg or "all" in lower_msg:
            try:
                summary = await self.tools.get_account_summary(user.customer_id)
            except Exception:
                summary = await self.service.get_account_summary(user.customer_id)
            formatted = format_currency(summary.total_balance_inr)
            return (
                f"Namaste {user.name}, you have {summary.account_count} account(s) with a total net balance of "
                f"{formatted}. Status: {summary.status}."
            )

        # 2. Specific Balance / List Accounts Tool Call
        try:
            acc_list = await self.tools.get_accounts(user.customer_id)
        except Exception:
            acc_list = await self.service.get_accounts_by_customer(user.customer_id)

        if not acc_list.accounts:
            return "No active accounts found for your customer ID."

        lines = [f"Here are your account details, {user.name}:"]
        for acc in acc_list.accounts:
            bal = format_currency(acc.balance, acc.currency)
            lines.append(f"- **{acc.account_type.title()} Account** ({acc.account_number}): {bal} [{acc.status}]")

        return "\n".join(lines)
