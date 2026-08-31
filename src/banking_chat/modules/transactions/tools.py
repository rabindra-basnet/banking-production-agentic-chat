"""Transactions tool definitions and client callers for MCP/Local execution."""

from __future__ import annotations

from typing import Any

import httpx

from banking_chat.core.common.exceptions import ToolExecutionError
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.transactions.schemas import (
    SpendingSummaryResponse,
    TransactionListResponse,
    TransactionQueryRequest,
)


class TransactionsTools:
    """Tool invocation wrapper for Transactions operations."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_transactions_url

    async def get_transactions(
        self, customer_id: str, query: TransactionQueryRequest | None = None
    ) -> TransactionListResponse:
        """Call transactions MCP server to fetch recent transactions."""
        url = f"{self.mcp_url}/tools/get_transactions"
        payload: dict[str, Any] = {"customer_id": customer_id}
        if query:
            payload["query"] = query.model_dump(mode="json")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return TransactionListResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("get_transactions", str(err)) from err

        raise ToolExecutionError("get_transactions", f"HTTP {resp.status_code}: {resp.text}")

    async def get_spending_summary(self, customer_id: str, days: int = 30) -> SpendingSummaryResponse:
        """Call transactions MCP server to calculate spending summary."""
        url = f"{self.mcp_url}/tools/get_spending_summary"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"customer_id": customer_id, "days": days})
                if resp.status_code == 200:
                    return SpendingSummaryResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("get_spending_summary", str(err)) from err

        raise ToolExecutionError("get_spending_summary", f"HTTP {resp.status_code}: {resp.text}")
