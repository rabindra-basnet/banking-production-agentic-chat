"""Unit tests for the Service Agent."""

from __future__ import annotations

import pytest

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.services.agent import ServiceAgent


@pytest.mark.asyncio
async def test_service_agent_block_card(standard_user: AuthenticatedUser) -> None:
    agent = ServiceAgent()
    resp = await agent.run("Please block my card ending in 5678", standard_user)
    assert "Card Block Confirmation" in resp
    assert "5678" in resp


@pytest.mark.asyncio
async def test_service_agent_cheque_book(standard_user: AuthenticatedUser) -> None:
    agent = ServiceAgent()
    resp = await agent.run("I need a new cheque book", standard_user)
    assert "Cheque Book Request Submitted" in resp
