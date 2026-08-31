"""Accounts Feature Slice module."""

from __future__ import annotations

from banking_chat.modules.accounts.agent import AccountsAgent
from banking_chat.modules.accounts.models import BankAccountModel
from banking_chat.modules.accounts.prompts import ACCOUNTS_AGENT_SYSTEM_PROMPT
from banking_chat.modules.accounts.schemas import (
    AccountBalanceRequest,
    AccountBalanceResponse,
    AccountListResponse,
    AccountSummaryResponse,
)
from banking_chat.modules.accounts.service import AccountsService
from banking_chat.modules.accounts.tools import AccountsTools

__all__ = [
    "ACCOUNTS_AGENT_SYSTEM_PROMPT",
    "AccountBalanceRequest",
    "AccountBalanceResponse",
    "AccountListResponse",
    "AccountSummaryResponse",
    "AccountsAgent",
    "AccountsService",
    "AccountsTools",
    "BankAccountModel",
]
