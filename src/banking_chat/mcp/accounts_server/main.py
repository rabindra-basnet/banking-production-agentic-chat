"""Standalone FastMCP server application for Bank Accounts on Port 9001."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from banking_chat.mcp.accounts_server.handlers import AccountsMCPHandlers

app = FastAPI(title="Banking Accounts MCP Server", version="0.1.0")
handlers = AccountsMCPHandlers()


class AccountsRequest(BaseModel):
    """Payload for listing accounts."""

    customer_id: str = Field(description="Customer CIF")


class AccountBalancePayload(BaseModel):
    """Payload for checking balance."""

    customer_id: str = Field(description="Customer CIF")
    account_number: str = Field(description="Target account number")


@app.post("/tools/get_accounts")
async def get_accounts_tool(payload: AccountsRequest) -> dict[str, Any]:
    """MCP tool endpoint: get_accounts."""
    return await handlers.get_accounts(payload.customer_id)


@app.post("/tools/get_account_balance")
async def get_account_balance_tool(payload: AccountBalancePayload) -> dict[str, Any]:
    """MCP tool endpoint: get_account_balance."""
    return await handlers.get_account_balance(payload.customer_id, payload.account_number)


@app.post("/tools/get_account_summary")
async def get_account_summary_tool(payload: AccountsRequest) -> dict[str, Any]:
    """MCP tool endpoint: get_account_summary."""
    return await handlers.get_account_summary(payload.customer_id)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "banking-accounts-mcp", "port": "9001"}


def run_server() -> None:
    """Run the standalone MCP server on port 9001."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9001)


if __name__ == "__main__":
    run_server()
