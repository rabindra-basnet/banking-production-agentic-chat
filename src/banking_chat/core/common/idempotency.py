"""Idempotency key manager for preventing duplicate operations and responses in banking interactions."""

from __future__ import annotations

import json
from typing import Any

from banking_chat.modules.session_memory.redis_store import RedisSessionStore


class IdempotencyManager:
    """Manages cached request outcomes based on Idempotency-Key headers or message fingerprints."""

    def __init__(self, store: RedisSessionStore | None = None) -> None:
        self.store = store or RedisSessionStore()

    async def get_response(self, idempotency_key: str, customer_id: str) -> dict[str, Any] | None:
        """Fetch previously computed response for a given idempotency key."""
        if not idempotency_key:
            return None
        cache_key = f"idempotency:{customer_id}:{idempotency_key}"
        return await self.store.get_session(cache_key)

    async def save_response(
        self,
        idempotency_key: str,
        customer_id: str,
        response_data: dict[str, Any],
    ) -> None:
        """Store the response associated with the idempotency key."""
        if not idempotency_key:
            return
        cache_key = f"idempotency:{customer_id}:{idempotency_key}"
        await self.store.save_session(cache_key, response_data)
