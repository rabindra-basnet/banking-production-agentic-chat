"""Unit tests for SSO / Banking Login Flow."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app


@pytest.mark.asyncio
async def test_banking_login_cif() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "CIF908123", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "CIF908123"
        assert data["name"] == "Rabindra Basnet"
        assert len(data["accounts"]) == 2
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_banking_login_email() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "sita.shrestha@example.com.np", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "CIF908456"
        assert data["name"] == "Sita Shrestha"
        assert data["tier"] == "premium"
