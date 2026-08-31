"""Standalone FastMCP Streamable HTTP Microservice for Transactions (Port 9002)."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.mcpserver import MCPServer

from banking_chat.core.config.logging_config import setup_logging
from banking_chat.mcp.transactions.handlers import TransactionsMCPHandlers

logger = logging.getLogger("banking_chat.mcp.transactions")

# Instantiate MCPServer
mcp_server = MCPServer("banking-transactions-mcp")
handlers = TransactionsMCPHandlers()


@mcp_server.tool(description="Query transaction history for a customer")
async def get_transactions(customer_id: str, account_number: str | None = None, limit: int = 10) -> dict[str, Any]:
    """MCP tool: get_transactions."""
    logger.info(
        "Executing get_transactions for customer_id=%s, account=%s, limit=%d", customer_id, account_number, limit
    )
    query: dict[str, Any] = {"limit": limit}
    if account_number:
        query["account_number"] = account_number
    return await handlers.get_transactions(customer_id, query)


@mcp_server.tool(description="Fetch spending summary for a customer over N days")
async def get_spending_summary(customer_id: str, days: int = 30) -> dict[str, Any]:
    """MCP tool: get_spending_summary."""
    logger.info("Executing get_spending_summary for customer_id=%s, days=%d", customer_id, days)
    return await handlers.get_spending_summary(customer_id, days=days)


# Export the Streamable HTTP ASGI Starlette app
app = mcp_server.streamable_http_app()


def run_server() -> None:
    """Run the standalone Streamable HTTP MCP server on port 9002."""
    import uvicorn

    setup_logging(log_level="INFO", json_output=False)
    logger.info("Starting Banking Transactions Streamable HTTP MCP server on port 9002...")
    uvicorn.run(app, host="0.0.0.0", port=9002)


if __name__ == "__main__":
    run_server()
