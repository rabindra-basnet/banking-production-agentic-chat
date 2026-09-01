"""Database checkpointer for long-term LangGraph state persistence and session title management."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from banking_chat.core.db.session import get_session_factory
from banking_chat.modules.session_memory.models import ChatSessionModel


class PostgresCheckpointer:
    """Checkpointer saving and restoring graph execution checkpoints in PostgreSQL / SQLite."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db = db_session

    async def list_customer_sessions(self, customer_id: str) -> list[ChatSessionModel]:
        """Fetch all chat sessions owned by a specific customer, ordered by last update."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = (
                select(ChatSessionModel)
                .where(ChatSessionModel.customer_id == customer_id)
                .order_by(desc(ChatSessionModel.updated_at))
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def delete_session(self, session_id: str, customer_id: str) -> bool:
        """Delete a chat session owned by the authenticated customer."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = delete(ChatSessionModel).where(
                ChatSessionModel.session_id == session_id,
                ChatSessionModel.customer_id == customer_id,
            )
            result = await session.execute(stmt)
            await session.commit()
            count = getattr(result, "rowcount", 0)
            return bool(count and count > 0)

    async def save_checkpoint(
        self,
        session_id: str,
        customer_id: str,
        checkpoint_data: dict[str, Any],
        messages: list[dict[str, Any]],
    ) -> None:
        """Persist state checkpoint to database and auto-generate title if needed."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(ChatSessionModel).where(ChatSessionModel.session_id == session_id)
            result = await session.execute(stmt)
            record = result.scalars().first()

            # Auto-generate title from first user query
            first_user_content = next(
                (m.get("content") for m in messages if m.get("role") == "user"), None
            )
            derived_title = "New Conversation"
            if first_user_content:
                clean_text = first_user_content.strip()
                derived_title = clean_text[:30] + ("..." if len(clean_text) > 30 else "")

            if record:
                record.state_checkpoint = checkpoint_data
                record.messages = messages
                if record.title in ("New Conversation", f"Chat {session_id[:8]}") and derived_title != "New Conversation":
                    record.title = derived_title
            else:
                new_record = ChatSessionModel(
                    id=uuid4(),
                    session_id=session_id,
                    customer_id=customer_id,
                    title=derived_title,
                    messages=messages,
                    state_checkpoint=checkpoint_data,
                )
                session.add(new_record)

            await session.commit()

    async def load_checkpoint(self, session_id: str) -> dict[str, Any] | None:
        """Load state checkpoint from database."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(ChatSessionModel).where(ChatSessionModel.session_id == session_id)
            result = await session.execute(stmt)
            record = result.scalars().first()
            if record:
                return record.state_checkpoint
            return None

    async def get_session_record(self, session_id: str) -> ChatSessionModel | None:
        """Fetch full session record from database."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(ChatSessionModel).where(ChatSessionModel.session_id == session_id)
            result = await session.execute(stmt)
            return result.scalars().first()
