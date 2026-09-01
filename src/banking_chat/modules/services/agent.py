import logging
import re
from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.services.prompts import SERVICE_AGENT_SYSTEM_PROMPT
from banking_chat.modules.services.schemas import BlockCardRequest, CreateServiceRequestPayload
from banking_chat.modules.services.service import CustomerServicesService
from banking_chat.modules.services.tools import ServicesTools

logger = logging.getLogger("banking_chat.modules.services")


class ServiceAgent:
    """Specialized agent for customer service requests and card operations executing through ServicesTools."""

    def __init__(
        self,
        service: CustomerServicesService | None = None,
        tools: ServicesTools | None = None,
    ) -> None:
        self.service = service or CustomerServicesService()
        self.tools = tools or ServicesTools()
        self.system_prompt = SERVICE_AGENT_SYSTEM_PROMPT

    async def run(self, user_message: str, user: AuthenticatedUser, **kwargs: Any) -> str:
        """Process a service requests domain user query using domain tools."""
        logger.info(f"Processing service request for customer={user.customer_id}: '{user_message}'")
        lower = user_message.lower()

        history = kwargs.get("history") or []
        last_assistant_msg = next((m.get("content", "") for m in reversed(history) if m.get("role") == "assistant"), "")

        # 1. Emergency Card Block Tool Call
        if "block" in lower and ("card" in lower or "debit" in lower or "credit" in lower):
            match = re.search(r"\b(\d{4})\b", user_message)
            card_last_four = match.group(1) if match else "1234"
            card_payload = BlockCardRequest(
                card_last_four=card_last_four,
                reason="lost",
                block_type="permanent",
            )
            try:
                resp = await self.tools.block_card(user.customer_id, card_payload)
            except Exception:
                resp = await self.service.block_card(user.customer_id, card_payload)

            return f"🚨 **Card Block Confirmation**\n\n{resp.message}\nReference ID: `{resp.request_id}`."

        # 2. Multi-turn Cheque Book Request Flow with Confirmation & Account Disambiguation
        is_cheque_intent = "cheque" in lower or "check book" in lower or "checkbook" in lower
        was_awaiting_cheque_confirmation = (
            "Please confirm the details for your Cheque Book request" in last_assistant_msg
        )
        is_affirmative = any(w in lower for w in ["yes", "confirm", "proceed", "submit", "ok", "sure", "correct"])

        # Check if this is a confirmation follow-up turn
        if was_awaiting_cheque_confirmation and is_affirmative:
            # Extract previous parameters from context if available
            leaves_match = re.search(r"(\d+)\s*leaves", last_assistant_msg, re.IGNORECASE)
            leaves = leaves_match.group(1) if leaves_match else "25"

            account_match = re.search(r"\b(\d{10,16})\b", last_assistant_msg)
            account_num = (
                account_match.group(1)
                if account_match
                else (user.accounts[0].split()[0] if user.accounts else "Primary Account")
            )

            cheque_payload = CreateServiceRequestPayload(
                type="cheque_book",
                notes=f"Cheque book ({leaves} leaves) for account {account_num}",
            )
            try:
                raw_resp = await self.tools.create_service_request(user.customer_id, cheque_payload)
                req_id = raw_resp.get("request_id", "SRV-REQ-PENDING")
            except Exception:
                req = await self.service.create_service_request(user.customer_id, cheque_payload)
                req_id = req.request_id

            return (
                f"✅ **Cheque Book Request Submitted**\n\n"
                f"- **Request ID**: `{req_id}`\n"
                f"- **Account**: `{account_num}`\n"
                f"- **Leaves**: {leaves} leaves\n"
                f"- **Status**: Submitted / Processing\n"
                f"- **Estimated Delivery**: 2-3 banking days\n"
                f"- **Pickup / Delivery**: Designated Branch in Nepal"
            )

        if is_cheque_intent:
            # Detect requested leaf size (default to 25 leaves)
            leaves_match = re.search(r"\b(25|50|100)\b", user_message)
            leaves = leaves_match.group(1) if leaves_match else "25"

            # Check accounts for disambiguation
            user_accounts = user.accounts or ["0120100056781234 (Savings Khata)"]
            selected_account = user_accounts[0]

            # If user mentioned an account ending, match it
            for acc in user_accounts:
                acc_num = acc.split()[0]
                if acc_num[-4:] in user_message or acc_num in user_message:
                    selected_account = acc
                    break

            account_num = selected_account.split()[0]

            return (
                f"I can help you request a new Cheque Book! Please confirm the details for your Cheque Book request:\n\n"
                f"• **Account**: `{selected_account}`\n"
                f"• **Book Size**: {leaves} leaves (Standard)\n"
                f"• **Collection Branch**: Kathmandu Main Branch (Nepal)\n"
                f"• **Service Charge**: Free for Standard Khata\n\n"
                f"👉 Would you like me to submit this request? Reply **'Yes, proceed'** to confirm."
            )

        # 3. List Existing Service Requests Tool Call
        try:
            req_list = await self.tools.get_service_requests(user.customer_id)
        except Exception:
            req_list = await self.service.get_service_requests(user.customer_id)

        if not req_list.requests:
            return "You have no active customer service requests at this moment."

        lines = ["Here are your active service requests:"]
        for r in req_list.requests:
            sub_date = (
                r.submitted_at.strftime("%d %b %Y") if hasattr(r.submitted_at, "strftime") else str(r.submitted_at)
            )
            lines.append(
                f"- **{r.type.replace('_', ' ').title()}** (`{r.request_id}`): {r.status} (Submitted: {sub_date})"
            )

        return "\n".join(lines)
