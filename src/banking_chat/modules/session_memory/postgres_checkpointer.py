"""PostgreSQL checkpointer for long-term LangGraph state persistence."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from banking_chat.modules.session_memory.models import ChatSessionModel


class PostgresCheckpointer:
    """Checkpointer saving and restoring graph execution checkpoints in PostgreSQL."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db = db_session

    async def save_checkpoint(
        self,
        session_id: str,
        customer_id: str,
        checkpoint_data: dict[str, Any],
        messages: list[dict[str, Any]],
    ) -> None:
        """Persist state checkpoint to database."""
        if self.db is None:
            return

        stmt = select(ChatSessionModel).where(ChatSessionModel.session_id == session_id)
        result = await self.db.execute(stmt)
        record = result.scalars().first()

        if record:
            record.state_checkpoint = checkpoint_data
            record.messages = messages
        else:
            new_record = ChatSessionModel(
                session_id=session_id,
                customer_id=customer_id,
                title=f"Chat {session_id[:8]}",
                messages=messages,
                state_checkpoint=checkpoint_data,
            )
            self.db.add(new_record)

        await self.db.flush()

    async def load_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        """Load state checkpoint from database."""
        if self.db is None:
            return None

        stmt = select(ChatSessionModel).where(ChatSessionModel.session_id == session_id)
        result = await self.db.execute(stmt)
        record = result.scalars().first()
        if record:
            return record.state_checkpoint
        return None
