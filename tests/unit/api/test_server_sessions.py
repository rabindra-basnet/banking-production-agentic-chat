"""Unit tests for Server-Side Database Chat Session Management."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.core.common.types import CustomerTier
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager
from banking_chat.core.db.session import get_engine
from banking_chat.core.db.base import Base


@pytest.mark.asyncio
async def test_list_and_delete_server_sessions() -> None:
    # Ensure database schema is created
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    validator = JWTValidator()
    pair = validator.create_token_pair(
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
    )
    access_token = str(pair["access_token"])

    # Create dummy session in backend memory/db
    mem = ConversationMemoryManager()
    session_id = "test-session-uuid-12345"
    await mem.append_message(
        session_id=session_id,
        customer_id="CIF908123",
        role="user",
        content="What is my account balance?",
    )

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        client.cookies.set("access_token", access_token)

        # 1. List sessions from backend
        resp = await client.get("/api/v1/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data
        assert any(s["id"] == session_id for s in data["sessions"])

        # 2. Get history from backend
        h_resp = await client.get(f"/api/v1/history/{session_id}")
        assert h_resp.status_code == 200
        h_data = h_resp.json()
        assert len(h_data["messages"]) > 0
        assert h_data["title"] == "What is my account balance?"

        # 3. Delete session from backend
        d_resp = await client.delete(f"/api/v1/sessions/{session_id}")
        assert d_resp.status_code == 200
