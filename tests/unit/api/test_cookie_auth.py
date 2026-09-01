"""Unit tests for Cookie-based Authentication."""

import pytest
from httpx import AsyncClient, ASGITransport
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
        
        # Access token and refresh token MUST NOT be exposed in the response body
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert data["customer_id"] == "CIF908123"
        assert data["name"] == "Rabindra Basnet"

        # Cookies must be set
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

        # Subsequent chat request works seamlessly with cookies
        chat_resp = await client.post(
            "/api/v1/chat",
            json={"message": "What is my balance?", "stream": False},
        )
        assert chat_resp.status_code == 200
        assert "Rabindra" in chat_resp.json()["message"]
