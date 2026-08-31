"""MCP tool handlers for Transactions microservice."""

from __future__ import annotations

from typing import Any

from banking_chat.modules.transactions.schemas import TransactionQueryRequest
from banking_chat.modules.transactions.service import TransactionsService


class TransactionsMCPHandlers:
    """Tool execution handlers exposed via Transactions FastMCP Server."""

    def __init__(self, service: TransactionsService | None = None) -> None:
        self.service = service or TransactionsService()

    async def get_transactions(
        self, customer_id: str, query: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Fetch transactions for customer."""
        req = TransactionQueryRequest.model_validate(query) if query else None
        res = await self.service.get_transactions(customer_id, req)
        result: dict[str, Any] = res.model_dump(mode="json")
        return result

    async def get_spending_summary(self, customer_id: str, days: int = 30) -> dict[str, Any]:
        """Fetch spending breakdown."""
        res = await self.service.get_spending_summary(customer_id, days)
        result: dict[str, Any] = res.model_dump(mode="json")
        return result
