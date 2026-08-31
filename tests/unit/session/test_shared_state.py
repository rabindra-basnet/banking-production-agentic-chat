"""Unit tests for Redis session store."""

from __future__ import annotations

import pytest

from banking_chat.modules.session_memory.redis_store import RedisSessionStore


@pytest.mark.asyncio
async def test_redis_session_store_lifecycle() -> None:
    store = RedisSessionStore()
    session_id = "session-test-456"

    await store.save_session(session_id, {"tier": "premium", "step": 1})
    data = await store.get_session(session_id)
    assert data is not None
    assert data["tier"] == "premium"
    assert data["step"] == 1

    await store.delete_session(session_id)
    deleted_data = await store.get_session(session_id)
    assert deleted_data is None
