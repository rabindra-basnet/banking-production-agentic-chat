import logging
import re
from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.core.common.utils import format_currency
from banking_chat.modules.accounts.prompts import ACCOUNTS_AGENT_SYSTEM_PROMPT
from banking_chat.modules.accounts.service import AccountsService
from banking_chat.modules.accounts.tools import AccountsTools

logger = logging.getLogger("banking_chat.modules.accounts")

# SQL / code injection patterns that should NEVER trigger bank tool calls
_INJECTION_PATTERNS = re.compile(
    r"\b(alter\s+table|drop\s+table|drop\s+database|select\s+\*|insert\s+into|"
    r"delete\s+from|update\s+\w+\s+set|union\s+select|exec\s*\(|"
    r"script>|<\s*img|javascript:|eval\s*\(|os\.system)\b",
    re.IGNORECASE,
)

# Keywords that indicate the user genuinely wants account / balance information
_ACCOUNTS_INTENT_KEYWORDS = [
    "balance",
    "account",
    "accounts",
    "saving",
    "savings",
    "khata",
    "muddati",
    "fixed deposit",
    "fd",
    "current",
    "holdings",
    "details",
    "how much",
    "kitna",
    "kati",
    "paisa",
    "money",
    "rupee",
    "rupees",
    "npr",
    "branch",
    "show",
    "list",
    "check",
    "my account",
]


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
        lower_msg = user_message.lower().strip()

        # 0. Security: Block injection / non-banking system commands
        if _INJECTION_PATTERNS.search(user_message):
            logger.warning(f"Blocked suspicious input from customer={user.customer_id}: '{user_message}'")
            return (
                "I'm sorry, I can only assist with banking-related queries. "
                "Please ask me about your account balance, transactions, cheque books, or other banking services."
            )

        # 1. Identity & Capability Questions
        if any(w in lower_msg for w in ["who are you", "what is your name", "what can you do", "help"]):
            return (
                f"Namaste **{user.name}**! 🙏\n\n"
                f"I am the **NepalBank AI Assistant**, your official retail banking concierge.\n\n"
                f"Here is what I can assist you with:\n\n"
                f"| Service | Description |\n"
                f"|---------|-------------|\n"
                f"| 💳 **Accounts & Balances** | Check Savings Khata, Muddati Khata & statements |\n"
                f"| 💸 **Payments & Transfers** | Fonepay QR queries, ConnectIPS transfers & spending history |\n"
                f"| 📋 **Banking Services** | Request Cheque Books (25/50/100 leaves), emergency card blocking & KYC updates |\n\n"
                f"How may I help you today?"
            )

        # 2. Greetings (hello, hi, namaste) — friendly response without data dump
        if lower_msg in ("hello", "hi", "namaste", "hey", "good morning", "good evening"):
            return f"Namaste **{user.name}**! 🙏 How can I assist you with your banking today?"

        # 3. Summary / Total Balance Tool Call
        if "summary" in lower_msg or "total" in lower_msg or ("all" in lower_msg and "account" in lower_msg):
            try:
                summary = await self.tools.get_account_summary(user.customer_id)
            except Exception:
                summary = await self.service.get_account_summary(user.customer_id)
            formatted = format_currency(summary.total_balance_inr)
            return (
                f"Namaste {user.name}, you have **{summary.account_count} account(s)** "
                f"with a total net balance of **{formatted}**.\n\n"
                f"Status: `{summary.status}`"
            )

        # 4. Specific Balance / List Accounts — ONLY if user asks for banking info
        has_accounts_intent = any(kw in lower_msg for kw in _ACCOUNTS_INTENT_KEYWORDS)

        if has_accounts_intent:
            try:
                acc_list = await self.tools.get_accounts(user.customer_id)
            except Exception:
                acc_list = await self.service.get_accounts_by_customer(user.customer_id)

            if not acc_list.accounts:
                return "No active accounts found for your customer ID."

            lines = [f"Here are your account details, **{user.name}**:\n"]
            lines.append("| Account | Number | Balance | Status |")
            lines.append("|---------|--------|---------|--------|")
            for acc in acc_list.accounts:
                bal = format_currency(acc.balance, acc.currency)
                acc_type = acc.account_type.replace("_", " ").title()
                lines.append(f"| {acc_type} | `{acc.account_number}` | **{bal}** | {acc.status} |")
            return "\n".join(lines)

        # 5. Fallback: Unrecognized non-banking query — polite redirect
        logger.info(f"Unrecognized query from customer={user.customer_id}: '{user_message}'")
        return (
            f"I'm not sure I understand that request, {user.name}. "
            f"I can help you with:\n\n"
            f'- 💳 **Account balance** — *"What is my account balance?"*\n'
            f'- 💸 **Transaction history** — *"Show my recent transactions"*\n'
            f'- 📋 **Cheque book request** — *"I want a new cheque book"*\n'
            f'- 🚨 **Card blocking** — *"Block my card ending in 5678"*\n\n'
            f"Please try one of these, or type **help** for more details."
        )

    async def get_tool_data(
        self,
        user_message: str,
        user: AuthenticatedUser,
        **kwargs: Any,
    ) -> dict[str, Any] | None:
        """Return structured tool data for LLM synthesis, or None if run() already has a definitive answer."""
        lower_msg = user_message.lower().strip()

        if _INJECTION_PATTERNS.search(user_message):
            return None

        if any(w in lower_msg for w in ["who are you", "what is your name", "what can you do", "help"]):
            return None
        if lower_msg in ("hello", "hi", "namaste", "hey", "good morning", "good evening"):
            return None

        # Summary
        if "summary" in lower_msg or "total" in lower_msg or ("all" in lower_msg and "account" in lower_msg):
            try:
                summary = await self.tools.get_account_summary(user.customer_id)
            except Exception:
                summary = await self.service.get_account_summary(user.customer_id)
            return summary.model_dump()

        # Account list
        has_accounts_intent = any(kw in lower_msg for kw in _ACCOUNTS_INTENT_KEYWORDS)
        if has_accounts_intent:
            try:
                acc_list = await self.tools.get_accounts(user.customer_id)
            except Exception:
                acc_list = await self.service.get_accounts_by_customer(user.customer_id)
            if not acc_list.accounts:
                return None
            return {
                "customer_name": user.name,
                "accounts": [acc.model_dump() for acc in acc_list.accounts],
            }

        return None
