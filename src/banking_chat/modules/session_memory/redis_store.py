"""Redis-backed session cache with in-memory fallback (dev only)."""

from __future__ import annotations

import json
import logging
from contextlib import suppress
from typing import Any

import redis.asyncio as aioredis

from banking_chat.core.config.settings import get_settings

logger = logging.getLogger("banking_chat.modules.session_memory.redis")


class RedisUnavailableError(RuntimeError):
    """Raised when a mandatory production dependency (Redis) is unreachable."""


class RedisSessionStore:
    """Fast cache for active conversation states and session tokens backed by real Redis.

    In development, falls back to an in-memory cache when Redis is offline.
    In production, Redis is mandatory: startup and runtime failures are fatal.
    """

    def __init__(self, redis_url: str | None = None, ttl_seconds: int | None = None) -> None:
        settings = get_settings()
        self.env = settings.app_env
        self.redis_url = redis_url or settings.redis_url
        self.ttl_seconds = ttl_seconds or settings.redis_session_ttl_seconds
        self._client: aioredis.Redis[Any] | None = None
        self._memory_cache: dict[str, str] = {}
        self._redis_available = True

    @property
    def _fallback_allowed(self) -> bool:
        """In-memory fallback is only permitted outside of production."""
        return self.env != "production"

    async def _get_client(self) -> aioredis.Redis[Any] | None:
        """Lazy-init Redis client; fall back to in-memory in dev or raise in production."""
        if not self._redis_available:
            return None
        if self._client is None:
            try:
                self._client = aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=5,
                )
                await self._client.ping()
                logger.info("Redis connection established: %s", self.redis_url)
            except Exception as exc:
                if not self._fallback_allowed:
                    logger.critical(
                        "Redis unavailable in %s environment (%s). Redis is mandatory for production; shutting down.",
                        self.env,
                        exc,
                    )
                    raise RedisUnavailableError(
                        f"Redis is required in {self.env} environment but is unreachable: {exc}"
                    ) from exc
                logger.warning("Redis unavailable (%s), falling back to in-memory cache", exc)
                self._redis_available = False
                self._client = None
                return None
        return self._client

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Retrieve cached session state."""
        client = await self._get_client()
        if client is not None:
            try:
                raw = await client.get(f"session:{session_id}")
                if raw is None:
                    return None
                data: dict[str, Any] = json.loads(raw)
                return data
            except Exception as exc:
                if not self._fallback_allowed:
                    logger.critical("Redis GET failed for session %s in %s: %s", session_id, self.env, exc)
                    raise RedisUnavailableError(f"Redis GET failed for session {session_id}: {exc}") from exc
                logger.warning("Redis GET failed for session %s: %s", session_id, exc)

        # In-memory fallback
        raw = self._memory_cache.get(f"session:{session_id}")
        if raw is None:
            return None
        cached: dict[str, Any] = json.loads(raw)
        return cached

    async def save_session(self, session_id: str, data: dict[str, Any]) -> None:
        """Store session state with TTL expiration."""
        payload = json.dumps(data)
        client = await self._get_client()
        if client is not None:
            try:
                await client.setex(f"session:{session_id}", self.ttl_seconds, payload)
                return
            except Exception as exc:
                if not self._fallback_allowed:
                    logger.critical("Redis SETEX failed for session %s in %s: %s", session_id, self.env, exc)
                    raise RedisUnavailableError(f"Redis SETEX failed for session {session_id}: {exc}") from exc
                logger.warning("Redis SETEX failed for session %s: %s", session_id, exc)

        # In-memory fallback
        self._memory_cache[f"session:{session_id}"] = payload

    async def delete_session(self, session_id: str) -> None:
        """Evict session state from cache."""
        client = await self._get_client()
        if client is not None:
            try:
                await client.delete(f"session:{session_id}")
                return
            except Exception as exc:
                if not self._fallback_allowed:
                    logger.critical("Redis DELETE failed for session %s in %s: %s", session_id, self.env, exc)
                    raise RedisUnavailableError(f"Redis DELETE failed for session {session_id}: {exc}") from exc
                logger.warning("Redis DELETE failed for session %s: %s", session_id, exc)

        self._memory_cache.pop(f"session:{session_id}", None)

    async def close(self) -> None:
        """Gracefully close Redis connection."""
        if self._client is not None:
            with suppress(Exception):
                await self._client.close()
            self._client = None
