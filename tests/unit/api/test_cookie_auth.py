"""Unit tests for Cookie-based Authentication."""

import pytest
from httpx import ASGITransport, AsyncClient

from banking_chat.main import app


@pytest.mark.asyncio
async def test_login_sets_httponly_cookies_and_clean_body() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "CIF908123", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()

        # Access token is returned for JS in-memory storage, refresh token in HttpOnly cookie
        assert "access_token" in data
        assert data["customer_id"] == "CIF908123"
        assert data["name"] == "Rabindra Basnet"

        # Refresh cookie must be set
        assert "refresh_token" in resp.cookies

        # Subsequent chat request works with Authorization header
        chat_resp = await client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {data['access_token']}"},
            json={"message": "What is my balance?", "stream": False},
        )
        assert chat_resp.status_code == 200
        body = chat_resp.json()
        assert "message" in body
        # LLM-generated response contains banking content (account balance data)
        assert len(body["message"]) > 20
        assert body["routed_agent"] in ("accounts_agent", "transaction_agent", "service_agent")
        assert isinstance(body["cost_usd"], float)
        assert isinstance(body["latency_ms"], float)
