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
async def test_service_agent_cheque_book_multiturn(standard_user: AuthenticatedUser) -> None:
    agent = ServiceAgent()
    # Turn 1: Initial request triggers confirmation details prompt
    prompt_resp = await agent.run("I want to request a new Cheque Book (25 leaves)", standard_user)
    assert "Please confirm the details for your Cheque Book request" in prompt_resp
    assert "25 leaves" in prompt_resp

    # Turn 2: User confirms -> Service request executed
    history = [
        {"role": "user", "content": "I want to request a new Cheque Book (25 leaves)"},
        {"role": "assistant", "content": prompt_resp},
    ]
    confirm_resp = await agent.run("Yes, proceed", standard_user, history=history)
    assert "Cheque Book Request Submitted" in confirm_resp
    assert "25 leaves" in confirm_resp
