"""End-to-end chat flow tests using FastAPI TestClient / AsyncClient."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from banking_chat.main import app


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
async def test_chat_flow_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/chat",
            json={"message": "What is my account balance?"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert "routed_agent" in data
