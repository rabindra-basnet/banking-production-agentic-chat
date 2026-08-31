"""Standalone FastMCP Streamable HTTP Microservice for Bank Accounts (Port 9001)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from banking_chat.core.config.logging_config import setup_logging
from banking_chat.mcp.accounts.handlers import AccountsMCPHandlers

logger = logging.getLogger("banking_chat.mcp.accounts")

# Instantiate MCPServer
mcp_server = MCPServer("banking-accounts-mcp")
handlers = AccountsMCPHandlers()


@mcp_server.tool(description="Fetch all accounts owned by a customer")
async def get_accounts(customer_id: str) -> dict[str, Any]:
    """MCP tool: get_accounts."""
    logger.info("Executing get_accounts for customer_id=%s", customer_id)
    return await handlers.get_accounts(customer_id)


@mcp_server.tool(description="Fetch balance for a specific account")
async def get_account_balance(customer_id: str, account_number: str) -> dict[str, Any]:
    """MCP tool: get_account_balance."""
    logger.info("Executing get_account_balance for customer_id=%s, account_number=%s", customer_id, account_number)
    return await handlers.get_account_balance(customer_id, account_number)


@mcp_server.tool(description="Fetch consolidated account summary for a customer")
async def get_account_summary(customer_id: str) -> dict[str, Any]:
    """MCP tool: get_account_summary."""
    logger.info("Executing get_account_summary for customer_id=%s", customer_id)
    return await handlers.get_account_summary(customer_id)


# Export the Streamable HTTP ASGI Starlette app
app = mcp_server.streamable_http_app()


def run_server() -> None:
    """Run the standalone Streamable HTTP MCP server on port 9001."""
    import uvicorn

    setup_logging(log_level="INFO", json_output=False)
    logger.info("Starting Banking Accounts Streamable HTTP MCP server on port 9001...")
    uvicorn.run(app, host="0.0.0.0", port=9001)


if __name__ == "__main__":
    run_server()
