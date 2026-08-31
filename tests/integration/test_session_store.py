"""Integration tests for session store."""

from __future__ import annotations

import pytest

from banking_chat.modules.session_memory.conversation import ConversationMemoryManager
from banking_chat.modules.session_memory.redis_store import RedisSessionStore


@pytest.mark.asyncio
async def test_session_store_integration() -> None:
    redis_store = RedisSessionStore()
    memory = ConversationMemoryManager(redis_store=redis_store)
    session_id = "integration-sess-001"

    await memory.append_message(session_id, "CIF001", "user", "What is my balance?")
    history = await memory.get_history(session_id)
    assert len(history) == 1
    assert history[0]["content"] == "What is my balance?"
