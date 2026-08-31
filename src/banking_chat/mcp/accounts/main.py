"""Standalone FastMCP Streamable HTTP Microservice for Bank Accounts (Port 9001)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from banking_chat.core.common.validators import mask_account_number
from banking_chat.core.config.logging_config import setup_logging
from banking_chat.core.config.settings import get_settings
from banking_chat.mcp.accounts.handlers import AccountsMCPHandlers

logger = logging.getLogger("banking_chat.mcp.accounts")

# Instantiate MCPServer
mcp_server = MCPServer("banking-accounts-mcp")
handlers = AccountsMCPHandlers()


@mcp_server.tool(description="Fetch all accounts owned by a customer")
async def get_accounts(customer_id: str) -> dict[str, Any]:
    """MCP tool: get_accounts."""
    logger.info("Executing get_accounts for customer [REDACTED]")
    return await handlers.get_accounts(customer_id)


@mcp_server.tool(description="Fetch balance for a specific account")
async def get_account_balance(customer_id: str, account_number: str) -> dict[str, Any]:
    """MCP tool: get_account_balance."""
    masked = mask_account_number(account_number)
    logger.info("Executing get_account_balance for account %s", masked)
    return await handlers.get_account_balance(customer_id, account_number)


@mcp_server.tool(description="Fetch consolidated account summary for a customer")
async def get_account_summary(customer_id: str) -> dict[str, Any]:
    """MCP tool: get_account_summary."""
    logger.info("Executing get_account_summary for customer [REDACTED]")
    return await handlers.get_account_summary(customer_id)


# Configure Transport Security allowing container service-name routing in Docker/Podman/K8s
transport_security = TransportSecuritySettings(
    allowed_hosts=["*"],
    allowed_origins=["*"],
    enable_dns_rebinding_protection=False,
)

# Export the Streamable HTTP ASGI Starlette app with security settings
app = mcp_server.streamable_http_app(transport_security=transport_security)


def run_server() -> None:
    """Run the standalone Streamable HTTP MCP server on port 9001."""
    import uvicorn

    settings = get_settings()
    setup_logging(log_level=settings.app_log_level, json_output=settings.app_env == "production")
    logger.info("Starting Banking Accounts Streamable HTTP MCP server on port 9001...")
    uvicorn.run(app, host="0.0.0.0", port=9001)


if __name__ == "__main__":
    run_server()
