"""Unit tests for the Accounts Agent."""

from __future__ import annotations

import pytest

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.accounts.agent import AccountsAgent


@pytest.mark.asyncio
async def test_accounts_agent_balance_check(standard_user: AuthenticatedUser) -> None:
    agent = AccountsAgent()
    resp = await agent.run("What is my account balance?", standard_user)
    assert "Here are your account details" in resp
    assert standard_user.name in resp


@pytest.mark.asyncio
async def test_accounts_agent_summary(standard_user: AuthenticatedUser) -> None:
    agent = AccountsAgent()
    resp = await agent.run("Show my total balance summary", standard_user)
    assert "total net balance" in resp
