"""MCP tool handlers for Accounts microservice."""

from __future__ import annotations

from typing import Any

from banking_chat.modules.accounts.service import AccountsService


class AccountsMCPHandlers:
    """Tool execution handlers exposed via Accounts FastMCP Server."""

    def __init__(self, service: AccountsService | None = None) -> None:
        self.service = service or AccountsService()

    async def get_accounts(self, customer_id: str) -> dict[str, Any]:
        res = await self.service.get_accounts_by_customer(customer_id)
        return res.model_dump(mode="json")

    async def get_account_balance(self, customer_id: str, account_number: str) -> dict[str, Any]:
        res = await self.service.get_account_balance(customer_id, account_number)
        return res.model_dump(mode="json")

    async def get_account_summary(self, customer_id: str) -> dict[str, Any]:
        res = await self.service.get_account_summary(customer_id)
        return res.model_dump(mode="json")
