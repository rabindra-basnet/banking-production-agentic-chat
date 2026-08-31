"""Standalone FastMCP server application for Customer Services on Port 9003."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from banking_chat.mcp_deployables.services_server.handlers import ServicesMCPHandlers

app = FastAPI(title="Banking Customer Services MCP Server", version="0.1.0")
handlers = ServicesMCPHandlers()


class ServicesRequest(BaseModel):
    """Payload for listing service requests."""

    customer_id: str = Field(description="Customer CIF")


class CreateServicePayload(BaseModel):
    """Payload for submitting a service request."""

    customer_id: str = Field(description="Customer CIF")
    type: str = Field(description="Type of request")
    notes: str | None = Field(default=None, description="Notes")


class BlockCardPayload(BaseModel):
    """Payload for card blocking."""

    customer_id: str = Field(description="Customer CIF")
    card_last_four: str = Field(description="Last 4 digits of card")
    reason: str = Field(default="lost", description="Reason for block")
    block_type: str = Field(default="permanent", description="Block type")


@app.post("/tools/get_service_requests")
async def get_service_requests_tool(payload: ServicesRequest) -> dict[str, Any]:
    """MCP tool endpoint: get_service_requests."""
    return await handlers.get_service_requests(payload.customer_id)


@app.post("/tools/create_service_request")
async def create_service_request_tool(payload: CreateServicePayload) -> dict[str, Any]:
    """MCP tool endpoint: create_service_request."""
    return await handlers.create_service_request(
        payload.customer_id,
        {"type": payload.type, "notes": payload.notes},
    )


@app.post("/tools/block_card")
async def block_card_tool(payload: BlockCardPayload) -> dict[str, Any]:
    """MCP tool endpoint: block_card."""
    return await handlers.block_card(
        payload.customer_id,
        {
            "card_last_four": payload.card_last_four,
            "reason": payload.reason,
            "block_type": payload.block_type,
        },
    )


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "banking-services-mcp", "port": "9003"}


def run_server() -> None:
    """Run the standalone MCP server on port 9003."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9003)


if __name__ == "__main__":
    run_server()
