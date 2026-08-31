"""Integration tests for standalone MCP servers."""

from __future__ import annotations

import pytest

from banking_chat.mcp.accounts.handlers import AccountsMCPHandlers
from banking_chat.mcp.services.handlers import ServicesMCPHandlers
from banking_chat.mcp.transactions.handlers import TransactionsMCPHandlers


@pytest.mark.asyncio
async def test_mcp_deployable_handlers() -> None:
    acc_handler = AccountsMCPHandlers()
    acc_res = await acc_handler.get_accounts("CIF001234")
    assert "accounts" in acc_res

    txn_handler = TransactionsMCPHandlers()
    txn_res = await txn_handler.get_transactions("CIF001234")
    assert "transactions" in txn_res

    srv_handler = ServicesMCPHandlers()
    srv_res = await srv_handler.get_service_requests("CIF001234")
    assert "requests" in srv_res
