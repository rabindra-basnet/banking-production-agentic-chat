"""Pydantic schemas for the accounts module."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from banking_chat.core.common.types import BankAccount


class AccountBalanceRequest(BaseModel):
    """Request payload to query account balance."""

    model_config = ConfigDict(strict=True)

    account_number: str = Field(description="Customer account number (full or masked)")


class AccountBalanceResponse(BaseModel):
    """Response payload for account balance query."""

    model_config = ConfigDict(strict=True)

    account_number: str = Field(description="Masked account number")
    account_type: str = Field(description="Type of account")
    balance: Decimal = Field(description="Current balance")
    currency: str = Field(default="INR", description="Currency ISO code")
    status: str = Field(description="Account status")


class AccountListResponse(BaseModel):
    """Response payload for listing customer accounts."""

    model_config = ConfigDict(strict=True)

    customer_id: str = Field(description="Customer CIF")
    accounts: list[BankAccount] = Field(description="List of accounts owned by customer")
    total_accounts: int = Field(description="Total account count")


class AccountSummaryResponse(BaseModel):
    """Summary of all customer accounts."""

    model_config = ConfigDict(strict=True)

    customer_id: str = Field(description="Customer CIF")
    total_balance_inr: Decimal = Field(description="Total net balance across accounts")
    account_count: int = Field(description="Number of accounts")
    account_types: list[str] = Field(description="Distinct account types held")
    status: Literal["active", "has_dormant", "has_frozen"] = Field(
        default="active", description="Aggregate account status"
    )
