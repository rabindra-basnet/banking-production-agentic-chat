"""Customer Services Agent implementation handling service requests and card blocking."""

from __future__ import annotations

import re
from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.services.prompts import SERVICE_AGENT_SYSTEM_PROMPT
from banking_chat.modules.services.schemas import BlockCardRequest, CreateServiceRequestPayload
from banking_chat.modules.services.service import CustomerServicesService


class ServiceAgent:
    """Specialized agent for customer service requests and card operations."""

    def __init__(self, service: CustomerServicesService | None = None) -> None:
        self.service = service or CustomerServicesService()
        self.system_prompt = SERVICE_AGENT_SYSTEM_PROMPT

    async def run(self, user_message: str, user: AuthenticatedUser, **kwargs: Any) -> str:
        """Process a service requests domain user query."""
        lower = user_message.lower()

        # Check for card block intent
        if "block" in lower and ("card" in lower or "debit" in lower or "credit" in lower):
            match = re.search(r"\b(\d{4})\b", user_message)
            card_last_four = match.group(1) if match else "1234"
            resp = await self.service.block_card(
                user.customer_id,
                BlockCardRequest(
                    card_last_four=card_last_four,
                    reason="lost",
                    block_type="permanent",
                ),
            )
            return f"🚨 **Card Block Confirmation**\n\n{resp.message}\nReference ID: `{resp.request_id}`."

        # Check for cheque book request
        if "cheque" in lower or "check book" in lower:
            req = await self.service.create_service_request(
                user.customer_id,
                CreateServiceRequestPayload(
                    type="cheque_book",
                    notes="Cheque book requested via chatbot",
                ),
            )
            est = req.estimated_completion.strftime("%d %b %Y") if req.estimated_completion else "3 business days"
            return (
                f"✅ **Cheque Book Request Submitted**\n\n"
                f"- Request ID: `{req.request_id}`\n"
                f"- Estimated Delivery: {est}\n"
                f"- Delivery Address: Registered Home Address"
            )

        # Default: list existing requests
        req_list = await self.service.get_service_requests(user.customer_id)
        if not req_list.requests:
            return "You have no active customer service requests at this moment."

        lines = ["Here are your active service requests:"]
        for r in req_list.requests:
            sub_date = r.submitted_at.strftime("%d %b %Y")
            lines.append(
                f"- **{r.type.replace('_', ' ').title()}** (`{r.request_id}`): {r.status} (Submitted: {sub_date})"
            )

        return "\n".join(lines)
