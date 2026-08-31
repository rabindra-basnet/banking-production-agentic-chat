"""Standalone FastMCP server application for Transactions on Port 9002."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from banking_chat.mcp.transactions.handlers import TransactionsMCPHandlers

app = FastAPI(title="Banking Transactions MCP Server", version="0.1.0")
handlers = TransactionsMCPHandlers()


class TransactionsRequest(BaseModel):
    customer_id: str = Field(description="Customer CIF")
    account_number: str | None = Field(default=None, description="Optional account filter")
    limit: int = Field(default=10, ge=1, le=100)


@app.post("/tools/get_transactions")
async def get_transactions_tool(payload: TransactionsRequest) -> dict[str, Any]:
    return await handlers.get_transactions(payload.customer_id, payload.model_dump())


@app.post("/tools/get_spending_summary")
async def get_spending_summary_tool(payload: TransactionsRequest) -> dict[str, Any]:
    return await handlers.get_spending_summary(payload.customer_id)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "banking-transactions-mcp", "port": "9002"}


def run_server() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9002)


if __name__ == "__main__":
    run_server()
