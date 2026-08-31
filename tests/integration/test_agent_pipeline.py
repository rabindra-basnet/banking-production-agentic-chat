"""Integration tests for the multi-agent chat pipeline."""

from __future__ import annotations

import pytest

from banking_chat.core.common.types import AuthenticatedUser
from banking_chat.modules.chat.graph import ChatPipeline


@pytest.mark.asyncio
async def test_chat_pipeline_execution(standard_user: AuthenticatedUser) -> None:
    pipeline = ChatPipeline()
    state = await pipeline.execute(
        session_id=str(standard_user.session_id),
        user_message="What is my account balance?",
        user=standard_user,
    )

    assert state["target_agent"] == "coordinator_agent" or "accounts" in state["target_agent"]
    assert len(state["final_response"]) > 0
    assert len(state["history"]) >= 2
