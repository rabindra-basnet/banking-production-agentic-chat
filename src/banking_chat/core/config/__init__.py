"""Configuration module for Banking Production Agentic Chat."""

from __future__ import annotations

from banking_chat.core.config.constants import (
    ACCOUNTS_AGENT,
    ACCOUNTS_MCP,
    API_V1_PREFIX,
    CHECKPOINT_INTERVAL,
    COORDINATOR_AGENT,
    DEFAULT_COST_HARD_LIMIT,
    DEFAULT_COST_WARNING_THRESHOLD,
    DEFAULT_SESSION_TTL,
    MAX_CONVERSATION_HISTORY,
    PII_TOKEN_PREFIX,
    PII_TOKEN_SUFFIX,
    RATE_LIMIT_BURST_ALLOWANCE,
    RATE_LIMIT_LOCKOUT_SECONDS,
    SERVICE_AGENT,
    SERVICES_MCP,
    TRANSACTION_AGENT,
    TRANSACTIONS_MCP,
)
from banking_chat.core.config.logging_config import setup_logging
from banking_chat.core.config.settings import Settings, get_settings

__all__ = [
    "ACCOUNTS_AGENT",
    "ACCOUNTS_MCP",
    "API_V1_PREFIX",
    "CHECKPOINT_INTERVAL",
    "COORDINATOR_AGENT",
    "DEFAULT_COST_HARD_LIMIT",
    "DEFAULT_COST_WARNING_THRESHOLD",
    "DEFAULT_SESSION_TTL",
    "MAX_CONVERSATION_HISTORY",
    "PII_TOKEN_PREFIX",
    "PII_TOKEN_SUFFIX",
    "RATE_LIMIT_BURST_ALLOWANCE",
    "RATE_LIMIT_LOCKOUT_SECONDS",
    "SERVICES_MCP",
    "SERVICE_AGENT",
    "TRANSACTIONS_MCP",
    "TRANSACTION_AGENT",
    "Settings",
    "get_settings",
    "setup_logging",
]
