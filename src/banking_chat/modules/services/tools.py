"""Customer services tool definitions and client callers for MCP/Local execution."""

from __future__ import annotations

import httpx

from banking_chat.core.common.exceptions import ToolExecutionError
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.services.schemas import (
    BlockCardRequest,
    BlockCardResponse,
    CreateServiceRequestPayload,
    ServiceRequestListResponse,
)


class ServicesTools:
    """Tool invocation wrapper for Customer Services operations."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_services_url

    async def get_service_requests(self, customer_id: str) -> ServiceRequestListResponse:
        """Call services MCP server to fetch list of customer service requests."""
        url = f"{self.mcp_url}/tools/get_service_requests"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"customer_id": customer_id})
                if resp.status_code == 200:
                    return ServiceRequestListResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("get_service_requests", str(err)) from err

        raise ToolExecutionError("get_service_requests", f"HTTP {resp.status_code}: {resp.text}")

    async def create_service_request(self, customer_id: str, payload: CreateServiceRequestPayload) -> dict[str, str]:
        """Call services MCP server to submit a new service request."""
        url = f"{self.mcp_url}/tools/create_service_request"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "customer_id": customer_id,
                        "type": payload.type,
                        "notes": payload.notes,
                    },
                )
                if resp.status_code == 200:
                    result: dict[str, str] = resp.json()
                    return result
        except Exception as err:
            raise ToolExecutionError("create_service_request", str(err)) from err

        raise ToolExecutionError("create_service_request", f"HTTP {resp.status_code}: {resp.text}")

    async def block_card(self, customer_id: str, payload: BlockCardRequest) -> BlockCardResponse:
        """Call services MCP server to block a card."""
        url = f"{self.mcp_url}/tools/block_card"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "customer_id": customer_id,
                        "card_last_four": payload.card_last_four,
                        "reason": payload.reason,
                        "block_type": payload.block_type,
                    },
                )
                if resp.status_code == 200:
                    return BlockCardResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("block_card", str(err)) from err

        raise ToolExecutionError("block_card", f"HTTP {resp.status_code}: {resp.text}")
