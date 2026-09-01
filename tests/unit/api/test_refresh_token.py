"""Unit tests for Refresh Token Endpoint with Cookies."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.core.common.types import CustomerTier


@pytest.mark.asyncio
async def test_auth_refresh_endpoint_cookie() -> None:
    validator = JWTValidator()
    pair = validator.create_token_pair(
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
        accounts=["0120100056781234", "0120100056785678"],
    )
    refresh_token = pair["refresh_token"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Pass refresh token in cookies
        client.cookies.set("refresh_token", refresh_token)
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["customer_id"] == "CIF908123"
        assert data["name"] == "Rabindra Basnet"
        assert "access_token" in data
        assert "refresh_token" in resp.cookies
