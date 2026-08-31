"""Pydantic schemas for the transactions module."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import Field

from banking_chat.core.common.types import StrictBaseModel, Transaction


class TransactionQueryRequest(StrictBaseModel):
    """Request payload to query transaction history."""

    account_number: str | None = Field(default=None, description="Optional account number filter")
    limit: int = Field(default=10, ge=1, le=100, description="Max transactions to return")
    transaction_type: Literal["credit", "debit", "all"] = Field(default="all", description="Filter by credit or debit")
    start_date: datetime | None = Field(default=None, description="Start date filter")
    end_date: datetime | None = Field(default=None, description="End date filter")


class TransactionListResponse(StrictBaseModel):
    """Response payload containing list of transactions."""

    customer_id: str = Field(description="Customer CIF")
    transactions: list[Transaction] = Field(description="List of transactions")
    total_count: int = Field(description="Total transactions returned")


class SpendingSummaryResponse(StrictBaseModel):
    """Summary of spending in a given period."""

    customer_id: str = Field(description="Customer CIF")
    total_spent: Decimal = Field(description="Total debits in period")
    total_received: Decimal = Field(description="Total credits in period")
    net_flow: Decimal = Field(description="Net cash flow")
    top_categories: dict[str, Decimal] = Field(default_factory=dict, description="Categorized spend breakdown")
