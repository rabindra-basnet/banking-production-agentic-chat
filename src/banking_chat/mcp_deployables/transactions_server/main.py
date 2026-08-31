"""Standalone FastMCP server application for Transactions on Port 9002."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from banking_chat.mcp_deployables.transactions_server.handlers import TransactionsMCPHandlers

app = FastAPI(title="Banking Transactions MCP Server", version="0.1.0")
handlers = TransactionsMCPHandlers()


class TransactionsRequest(BaseModel):
    """Payload for querying transactions."""

    customer_id: str = Field(description="Customer CIF")
    query: dict[str, Any] | None = Field(default=None, description="Optional query filter parameters")


class SpendingSummaryPayload(BaseModel):
    """Payload for spending summary."""

    customer_id: str = Field(description="Customer CIF")
    days: int = Field(default=30, description="Lookback days")


@app.post("/tools/get_transactions")
async def get_transactions_tool(payload: TransactionsRequest) -> dict[str, Any]:
    """MCP tool endpoint: get_transactions."""
    return await handlers.get_transactions(payload.customer_id, payload.query)


@app.post("/tools/get_spending_summary")
async def get_spending_summary_tool(payload: SpendingSummaryPayload) -> dict[str, Any]:
    """MCP tool endpoint: get_spending_summary."""
    return await handlers.get_spending_summary(payload.customer_id, payload.days)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "banking-transactions-mcp", "port": "9002"}


def run_server() -> None:
    """Run the standalone MCP server on port 9002."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9002)


if __name__ == "__main__":
    run_server()
