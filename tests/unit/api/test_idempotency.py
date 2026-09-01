"""Unit tests for Idempotent API calls."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app
from banking_chat.modules.auth.jwt_validator import JWTValidator


@pytest.mark.asyncio
async def test_chat_idempotency_same_key() -> None:
    token = JWTValidator().create_mock_token(customer_id="CIF908123")
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "test-idem-key-12345",
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First call
        resp1 = await client.post(
            "/api/v1/chat",
            json={"message": "What is my account balance?", "stream": False},
            headers=headers,
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["idempotency_key"] == "test-idem-key-12345"

        # Second duplicate call with same idempotency key
        resp2 = await client.post(
            "/api/v1/chat",
            json={"message": "What is my account balance?", "stream": False},
            headers=headers,
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["message"] == data1["message"]
        assert data2["routed_agent"] == data1["routed_agent"]
        assert data2["latency_ms"] == 0.0  # Served directly from cache
