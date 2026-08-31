"""Customer Services MCP Server deployable application."""

from __future__ import annotations

from banking_chat.mcp.services_server.handlers import ServicesMCPHandlers
from banking_chat.mcp.services_server.main import app

__all__ = ["ServicesMCPHandlers", "app"]
