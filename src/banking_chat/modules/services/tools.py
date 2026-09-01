"""Customer services tool definitions and client callers for MCP Streamable HTTP execution."""

from __future__ import annotations

from banking_chat.core.common.mcp_client import StreamableMCPClient
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.services.schemas import (
    BlockCardRequest,
    BlockCardResponse,
    CreateServiceRequestPayload,
    ServiceRequestListResponse,
)


class ServicesTools:
    """Tool invocation wrapper for Customer Services operations over Streamable MCP."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_services_url
        self.client = StreamableMCPClient(self.mcp_url)

    async def get_service_requests(self, customer_id: str) -> ServiceRequestListResponse:
        """Call services MCP server to fetch list of customer service requests."""
        res = await self.client.call_tool("get_service_requests", {"customer_id": customer_id})
        return ServiceRequestListResponse.model_validate(res)

    async def create_service_request(self, customer_id: str, payload: CreateServiceRequestPayload) -> dict[str, str]:
        """Call services MCP server to submit a new service request."""
        res = await self.client.call_tool(
            "create_service_request",
            {
                "customer_id": customer_id,
                "request_type": payload.type,
                "notes": payload.notes,
            },
        )
        return dict(res)

    async def block_card(self, customer_id: str, payload: BlockCardRequest) -> BlockCardResponse:
        """Call services MCP server to block a card."""
        res = await self.client.call_tool(
            "block_card",
            {
                "customer_id": customer_id,
                "card_last_four": payload.card_last_four,
                "reason": payload.reason,
                "block_type": payload.block_type,
            },
        )
        return BlockCardResponse.model_validate(res)
