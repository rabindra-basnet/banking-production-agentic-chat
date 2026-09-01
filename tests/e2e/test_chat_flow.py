"""End-to-end chat flow tests using FastAPI TestClient / AsyncClient across all domains."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_auth_refresh_token_flow() -> None:
    validator = JWTValidator()
    pair = validator.create_token_pair(customer_id="CIF908123", name="Rabindra Basnet")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.cookies.set("refresh_token", str(pair["refresh_token"]))
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"
        assert "customer_id" not in data
        assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_chat_flow_accounts_intent() -> None:
    session_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat",
            json={"message": "What is my savings account balance?", "session_id": str(session_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "account" in data["message"].lower()
        assert data["routed_agent"] == "accounts_agent"
        assert data["session_id"] == str(session_id)


@pytest.mark.asyncio
async def test_chat_flow_transactions_intent() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat",
            json={"message": "Show me my recent transactions and spending summary"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_agent"] == "transaction_agent"
        assert "transaction" in data["message"].lower() or "spending" in data["message"].lower()


@pytest.mark.asyncio
async def test_chat_flow_services_intent() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/chat",
            json={"message": "Please block my lost debit card ending in 1234"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["routed_agent"] == "service_agent"
        assert "block" in data["message"].lower() or "card" in data["message"].lower()


@pytest.mark.asyncio
async def test_conversation_history_persistence() -> None:
    session_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: Send message
        await client.post(
            "/api/v1/chat",
            json={"message": "What is my account balance?", "session_id": str(session_id)},
        )

        # Step 2: Fetch history
        resp = await client.get(f"/api/v1/history/{session_id}")
        assert resp.status_code == 200
        history_data = resp.json()
        assert history_data["session_id"] == str(session_id)
        assert len(history_data["messages"]) >= 2
        assert history_data["messages"][0]["role"] == "user"
        assert history_data["messages"][1]["role"] == "assistant"
