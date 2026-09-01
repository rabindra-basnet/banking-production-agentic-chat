"""Customer Services Agent implementation handling service requests via Services Tools."""

from __future__ import annotations

import re
from typing import Any

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.services.prompts import SERVICE_AGENT_SYSTEM_PROMPT
from banking_chat.modules.services.schemas import BlockCardRequest, CreateServiceRequestPayload
from banking_chat.modules.services.service import CustomerServicesService
from banking_chat.modules.services.tools import ServicesTools


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
        lower = user_message.lower()

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

        # 2. Cheque Book Service Request Tool Call
        if "cheque" in lower or "check book" in lower:
            cheque_payload = CreateServiceRequestPayload(
                type="cheque_book",
                notes="Cheque book requested via chatbot",
            )
            try:
                raw_resp = await self.tools.create_service_request(user.customer_id, cheque_payload)
                req_id = raw_resp.get("request_id", "SRV-REQ-PENDING")
            except Exception:
                req = await self.service.create_service_request(user.customer_id, cheque_payload)
                req_id = req.request_id

            return (
                f"✅ **Cheque Book Request Submitted**\n\n"
                f"- Request ID: `{req_id}`\n"
                f"- Status: Submitted / Processing\n"
                f"- Estimated Delivery: 2-3 banking days\n"
                f"- Pickup / Delivery: Designated Branch in Nepal"
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
            sub_date = r.submitted_at.strftime("%d %b %Y") if hasattr(r.submitted_at, "strftime") else str(r.submitted_at)
            lines.append(
                f"- **{r.type.replace('_', ' ').title()}** (`{r.request_id}`): {r.status} (Submitted: {sub_date})"
            )

        return "\n".join(lines)
