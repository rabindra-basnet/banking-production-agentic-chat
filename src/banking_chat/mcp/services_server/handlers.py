"""MCP tool handlers for Customer Services microservice."""

from __future__ import annotations

from typing import Any

from banking_chat.modules.services.schemas import BlockCardRequest, CreateServiceRequestPayload
from banking_chat.modules.services.service import CustomerServicesService


class ServicesMCPHandlers:
    """Tool execution handlers exposed via Services FastMCP Server."""

    def __init__(self, service: CustomerServicesService | None = None) -> None:
        self.service = service or CustomerServicesService()

    async def get_service_requests(self, customer_id: str) -> dict[str, Any]:
        """Fetch all service requests for a customer."""
        res = await self.service.get_service_requests(customer_id)
        return res.model_dump(mode="json")

    async def create_service_request(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Submit a new service request."""
        req = CreateServiceRequestPayload.model_validate(payload)
        res = await self.service.create_service_request(customer_id, req)
        return res.model_dump(mode="json")

    async def block_card(self, customer_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Block a customer card."""
        req = BlockCardRequest.model_validate(payload)
        res = await self.service.block_card(customer_id, req)
        return res.model_dump(mode="json")
