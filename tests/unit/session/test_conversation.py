"""Unit tests for conversation memory manager."""

from __future__ import annotations

import pytest

from banking_chat.modules.session_memory.conversation import ConversationMemoryManager


@pytest.mark.asyncio
async def test_conversation_memory_append_and_retrieve() -> None:
    manager = ConversationMemoryManager(max_history=5)
    session_id = "test-session-123"

    await manager.append_message(session_id, "CIF123", "user", "Hello")
    history = await manager.append_message(session_id, "CIF123", "assistant", "Hello, how can I help?")

    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hello, how can I help?"
