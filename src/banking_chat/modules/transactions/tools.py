"""Transactions tool definitions and client callers for MCP Streamable HTTP execution."""

from __future__ import annotations

from typing import Any

from banking_chat.core.common.mcp_client import StreamableMCPClient
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.transactions.schemas import (
    SpendingSummaryResponse,
    TransactionListResponse,
    TransactionQueryRequest,
)


class TransactionsTools:
    """Tool invocation wrapper for Transactions operations over Streamable MCP."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_transactions_url
        self.client = StreamableMCPClient(self.mcp_url)

    async def get_transactions(
        self, customer_id: str, query: TransactionQueryRequest | None = None
    ) -> TransactionListResponse:
        """Call transactions MCP server to fetch recent transactions."""
        args: dict[str, Any] = {"customer_id": customer_id}
        if query:
            if query.account_number:
                args["account_number"] = query.account_number
            if query.limit:
                args["limit"] = query.limit
        res = await self.client.call_tool("get_transactions", args)
        return TransactionListResponse.model_validate(res)

    async def get_spending_summary(self, customer_id: str, days: int = 30) -> SpendingSummaryResponse:
        """Call transactions MCP server to calculate spending summary."""
        res = await self.client.call_tool("get_spending_summary", {"customer_id": customer_id, "days": days})
        return SpendingSummaryResponse.model_validate(res)
