"""Standalone FastMCP Streamable HTTP Microservice for Customer Services (Port 9003)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from banking_chat.core.config.logging_config import setup_logging
from banking_chat.core.config.settings import get_settings
from banking_chat.mcp.services.handlers import ServicesMCPHandlers

logger = logging.getLogger("banking_chat.mcp.services")

# Instantiate MCPServer
mcp_server = MCPServer("banking-services-mcp")
handlers = ServicesMCPHandlers()


@mcp_server.tool(description="Fetch all service requests submitted by a customer")
async def get_service_requests(customer_id: str) -> dict[str, Any]:
    """MCP tool: get_service_requests."""
    logger.info("Executing get_service_requests for customer [REDACTED]")
    return await handlers.get_service_requests(customer_id)


@mcp_server.tool(description="Create a new service request (cheque book, address change, KYC, etc.)")
async def create_service_request(customer_id: str, request_type: str, notes: str | None = None) -> dict[str, Any]:
    """MCP tool: create_service_request."""
    logger.info("Executing create_service_request for customer [REDACTED], type=%s", request_type)
    return await handlers.create_service_request(customer_id, {"type": request_type, "notes": notes})


@mcp_server.tool(description="Block a customer debit or credit card")
async def block_card(
    customer_id: str, card_last_four: str, reason: str = "lost", block_type: str = "permanent"
) -> dict[str, Any]:
    """MCP tool: block_card."""
    logger.info("Executing block_card for customer [REDACTED], card=...%s, reason=%s", card_last_four, reason)
    return await handlers.block_card(
        customer_id,
        {"card_last_four": card_last_four, "reason": reason, "block_type": block_type},
    )


# Export the Streamable HTTP ASGI Starlette app
app = mcp_server.streamable_http_app()


def run_server() -> None:
    """Run the standalone Streamable HTTP MCP server on port 9003."""
    import uvicorn

    settings = get_settings()
    setup_logging(log_level=settings.app_log_level, json_output=settings.app_env == "production")
    logger.info("Starting Banking Customer Services Streamable HTTP MCP server on port 9003...")
    uvicorn.run(app, host="0.0.0.0", port=9003)


if __name__ == "__main__":
    run_server()
