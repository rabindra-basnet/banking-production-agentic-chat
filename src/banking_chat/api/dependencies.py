"""FastAPI dependency injection providers."""

from __future__ import annotations

from functools import lru_cache

from banking_chat.config.settings import Settings, get_settings


@lru_cache
def get_cached_settings() -> Settings:
    """Cached settings dependency for FastAPI."""
    return get_settings()


# TODO: Add dependencies for:
# - get_current_user (from auth middleware)
# - get_session_store (Redis client)
# - get_db_session (PostgreSQL async session)
# - get_mcp_clients (MCP server connections)
