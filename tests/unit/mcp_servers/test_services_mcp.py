"""Unit tests for Services MCP handlers."""

from __future__ import annotations

import pytest

from banking_chat.mcp.services_server.handlers import ServicesMCPHandlers


@pytest.mark.asyncio
async def test_services_mcp_handler() -> None:
    handlers = ServicesMCPHandlers()
    res = await handlers.get_service_requests("CIF001234")
    assert res["customer_id"] == "CIF001234"
    assert len(res["requests"]) > 0
