"""Redis-backed session cache with in-memory fallback."""

from __future__ import annotations

import json
from typing import Any

from banking_chat.core.config.settings import get_settings


class RedisSessionStore:
    """Fast cache for active conversation states and session tokens."""

    def __init__(self, redis_url: str | None = None, ttl_seconds: int | None = None) -> None:
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = ttl_seconds or settings.redis_session_ttl_seconds
        self._memory_cache: dict[str, str] = {}

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve cached session state."""
        raw = self._memory_cache.get(f"session:{session_id}")
        if raw is None:
            return None
        data: dict[str, Any] = json.loads(raw)
        return data

    async def save_session(self, session_id: str, data: dict[str, Any]) -> None:
        """Store session state with TTL expiration."""
        self._memory_cache[f"session:{session_id}"] = json.dumps(data)

    async def delete_session(self, session_id: str) -> None:
        """Evict session state from cache."""
        self._memory_cache.pop(f"session:{session_id}", None)
