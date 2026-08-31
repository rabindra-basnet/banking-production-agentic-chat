"""Conversation memory and message history management."""

from __future__ import annotations

from typing import Any

from banking_chat.core.config.constants import MAX_CONVERSATION_HISTORY
from banking_chat.modules.session_memory.postgres_checkpointer import PostgresCheckpointer
from banking_chat.modules.session_memory.redis_store import RedisSessionStore


class ConversationMemoryManager:
    """Manages short-term conversation context in Redis and long-term history in Postgres."""

    def __init__(
        self,
        redis_store: RedisSessionStore | None = None,
        checkpointer: PostgresCheckpointer | None = None,
        max_history: int = MAX_CONVERSATION_HISTORY,
    ) -> None:
        self.redis_store = redis_store or RedisSessionStore()
        self.checkpointer = checkpointer or PostgresCheckpointer()
        self.max_history = max_history

    async def get_history(self, session_id: str) -> list[dict[str, Any]]:
        """Retrieve recent conversation messages."""
        cached = await self.redis_store.get_session(session_id)
        if cached and "messages" in cached:
            messages: list[dict[str, Any]] = cached["messages"]
            return messages
        return []

    async def append_message(
        self, session_id: str, customer_id: str, role: str, content: str, **metadata: Any
    ) -> list[dict[str, Any]]:
        """Add a message to the conversation history and persist state."""
        messages = await self.get_history(session_id)
        new_msg: dict[str, Any] = {"role": role, "content": content, **metadata}
        messages.append(new_msg)

        if len(messages) > self.max_history:
            messages = messages[-self.max_history :]

        await self.redis_store.save_session(session_id, {"messages": messages})
        await self.checkpointer.save_checkpoint(
            session_id=session_id,
            customer_id=customer_id,
            checkpoint_data={"last_role": role},
            messages=messages,
        )
        return messages
