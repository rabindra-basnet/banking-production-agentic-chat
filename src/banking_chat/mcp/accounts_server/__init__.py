"""Accounts MCP Server deployable application."""

from __future__ import annotations

from banking_chat.mcp.accounts_server.handlers import AccountsMCPHandlers
from banking_chat.mcp.accounts_server.main import app

__all__ = ["AccountsMCPHandlers", "app"]
