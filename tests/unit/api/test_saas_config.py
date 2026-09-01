"""Unit tests for SaaS App Configuration Endpoint."""

import pytest
from httpx import AsyncClient, ASGITransport
from banking_chat.main import app


@pytest.mark.asyncio
async def test_get_app_config_endpoint() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "bank_name" in data
        assert "bank_tagline" in data
        assert "bank_badge" in data
        assert "assistant_name" in data
        assert "compliance_notice" in data
        assert "supported_services" in data
