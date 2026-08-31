"""Unit tests for the Transaction Agent."""

from __future__ import annotations

import pytest

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.transactions.agent import TransactionsAgent


@pytest.mark.asyncio
async def test_transactions_agent_list(standard_user: AuthenticatedUser) -> None:
    agent = TransactionsAgent()
    resp = await agent.run("Show my transactions", standard_user)
    assert "Here are your latest" in resp


@pytest.mark.asyncio
async def test_transactions_agent_spending(standard_user: AuthenticatedUser) -> None:
    agent = TransactionsAgent()
    resp = await agent.run("Show my 30 day spending summary", standard_user)
    assert "Spending Summary" in resp
