"""Accounts tool definitions and client callers for MCP/Local execution."""

from __future__ import annotations

import httpx

from banking_chat.core.common.exceptions import ToolExecutionError
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.accounts.schemas import (
    AccountBalanceResponse,
    AccountListResponse,
    AccountSummaryResponse,
)


class AccountsTools:
    """Tool invocation wrapper for Accounts operations."""

    def __init__(self, mcp_url: str | None = None) -> None:
        settings = get_settings()
        self.mcp_url = mcp_url or settings.mcp_accounts_url

    async def get_accounts(self, customer_id: str) -> AccountListResponse:
        """Call accounts MCP server to list accounts."""
        url = f"{self.mcp_url}/tools/get_accounts"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"customer_id": customer_id})
                if resp.status_code == 200:
                    return AccountListResponse.model_validate(resp.json())
        except Exception as err:
            # Tool invocation error or fallback
            raise ToolExecutionError("get_accounts", str(err)) from err

        raise ToolExecutionError("get_accounts", f"HTTP {resp.status_code}: {resp.text}")

    async def get_account_balance(self, customer_id: str, account_number: str) -> AccountBalanceResponse:
        """Call accounts MCP server to get account balance."""
        url = f"{self.mcp_url}/tools/get_account_balance"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"customer_id": customer_id, "account_number": account_number})
                if resp.status_code == 200:
                    return AccountBalanceResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("get_account_balance", str(err)) from err

        raise ToolExecutionError("get_account_balance", f"HTTP {resp.status_code}: {resp.text}")

    async def get_account_summary(self, customer_id: str) -> AccountSummaryResponse:
        """Call accounts MCP server to get account summary."""
        url = f"{self.mcp_url}/tools/get_account_summary"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"customer_id": customer_id})
                if resp.status_code == 200:
                    return AccountSummaryResponse.model_validate(resp.json())
        except Exception as err:
            raise ToolExecutionError("get_account_summary", str(err)) from err

        raise ToolExecutionError("get_account_summary", f"HTTP {resp.status_code}: {resp.text}")
