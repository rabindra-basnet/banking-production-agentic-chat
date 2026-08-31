"""Unit tests for Accounts MCP handlers."""

from __future__ import annotations

import pytest

from banking_chat.mcp.accounts_server.handlers import AccountsMCPHandlers


@pytest.mark.asyncio
async def test_accounts_mcp_handler() -> None:
    handlers = AccountsMCPHandlers()
    res = await handlers.get_accounts("CIF001234")
    assert res["customer_id"] == "CIF001234"
    assert len(res["accounts"]) > 0
