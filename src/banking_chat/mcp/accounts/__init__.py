"""Accounts MCP package."""

from __future__ import annotations

from banking_chat.mcp.accounts.handlers import AccountsMCPHandlers
from banking_chat.mcp.accounts.main import app

__all__ = ["AccountsMCPHandlers", "app"]
