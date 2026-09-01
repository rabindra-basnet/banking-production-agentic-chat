"""Accounts tool definitions and client callers for MCP Streamable HTTP execution."""

from __future__ import annotations

from banking_chat.core.common.mcp_client import StreamableMCPClient
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.accounts.schemas import (
    AccountBalanceResponse,
    AccountListResponse,
    AccountSummaryResponse,
)


class AccountsTools:
    """Tool invocation wrapper for Accounts operations over Streamable MCP."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_accounts_url
        self.client = StreamableMCPClient(self.mcp_url)

    async def get_accounts(self, customer_id: str) -> AccountListResponse:
        """Call accounts MCP server to list accounts."""
        res = await self.client.call_tool("get_accounts", {"customer_id": customer_id})
        return AccountListResponse.model_validate(res)

    async def get_account_balance(self, customer_id: str, account_number: str) -> AccountBalanceResponse:
        """Call accounts MCP server to get account balance."""
        res = await self.client.call_tool(
            "get_account_balance",
            {"customer_id": customer_id, "account_number": account_number},
        )
        return AccountBalanceResponse.model_validate(res)

    async def get_account_summary(self, customer_id: str) -> AccountSummaryResponse:
        """Call accounts MCP server to get account summary."""
        res = await self.client.call_tool("get_account_summary", {"customer_id": customer_id})
        return AccountSummaryResponse.model_validate(res)
