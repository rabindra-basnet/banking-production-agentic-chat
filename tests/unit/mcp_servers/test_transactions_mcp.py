"""Unit tests for Transactions MCP handlers."""

from __future__ import annotations

import pytest

from banking_chat.mcp.transactions.handlers import TransactionsMCPHandlers


@pytest.mark.asyncio
async def test_transactions_mcp_handler() -> None:
    handlers = TransactionsMCPHandlers()
    res = await handlers.get_transactions("CIF001234")
    assert res["customer_id"] == "CIF001234"
    assert len(res["transactions"]) > 0
