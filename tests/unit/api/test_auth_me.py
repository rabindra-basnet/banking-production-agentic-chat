"""Unit tests for /auth/me session check endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from banking_chat.core.common.types import CustomerTier
from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator


@pytest.mark.asyncio
async def test_auth_me_returns_profile_for_authenticated_cookies() -> None:
    validator = JWTValidator()
    pair = validator.create_token_pair(
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
    )
    access_token = str(pair["access_token"])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Pass access token via cookie
        client.cookies.set("access_token", access_token)
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "CIF908123"
        assert data["name"] == "Rabindra Basnet"
        assert len(data["accounts"]) == 2
