"""Unit tests for Logout and Token Blacklisting."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator
from banking_chat.core.common.types import CustomerTier


@pytest.mark.asyncio
async def test_logout_blacklists_tokens_and_prevents_subsequent_access() -> None:
    validator = JWTValidator()
    pair = validator.create_token_pair(
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
    )
    access_token = str(pair["access_token"])
    refresh_token = str(pair["refresh_token"])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Set cookies for authenticated user
        client.cookies.set("access_token", access_token)
        client.cookies.set("refresh_token", refresh_token)

        # Call logout endpoint
        logout_resp = await client.post("/api/v1/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json()["status"] == "logged_out"

        # Attempt to use blacklisted refresh token -> must fail
        refresh_fail_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_fail_resp.status_code == 401

        # Attempt to use blacklisted access token in Authorization header -> must fail
        chat_fail_resp = await client.post(
            "/api/v1/chat",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"message": "What is my balance?", "stream": False},
        )
        assert chat_fail_resp.status_code == 401
