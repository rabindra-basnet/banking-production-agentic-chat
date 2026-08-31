"""Shared type definitions and data models used across the application."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ─── Enums ───


class CustomerTier(StrEnum):
    """Customer authorization tier — determines accessible features."""

    STANDARD = "standard"
    PREMIUM = "premium"
    PRIVILEGED = "privileged"


class AgentName(StrEnum):
    """Names of available agents in the system."""

    COORDINATOR = "coordinator_agent"
    ACCOUNTS = "accounts_agent"
    TRANSACTION = "transaction_agent"
    SERVICE = "service_agent"


# ─── Authentication Models ───


class AuthenticatedUser(BaseModel):
    """Validated user identity from the bank's identity provider (IdP)."""

    model_config = ConfigDict(strict=True, frozen=True)

    user_id: UUID = Field(description="Unique customer identifier from bank's IdP")
    customer_id: str = Field(description="Bank's internal customer number (CIF)")
    name: str = Field(description="Customer's display name")
    email: str = Field(description="Verified email address")
    tier: CustomerTier = Field(description="Authorization tier")
    accounts: list[str] = Field(description="List of account numbers the customer owns")
    session_id: UUID = Field(description="Current chat session ID")
    token_expiry: datetime = Field(description="JWT token expiration timestamp")


# ─── Banking Entity Models ───


class BankAccount(BaseModel):
    """Bank account details returned by Accounts MCP Server."""

    model_config = ConfigDict(strict=True)

    account_number: str = Field(description="Masked account number (last 4 digits visible)")
    account_type: Literal["savings", "current", "fixed_deposit", "recurring_deposit"]
    balance: Decimal = Field(description="Current available balance")
    currency: str = Field(default="INR", description="Currency code (ISO 4217)")
    status: Literal["active", "dormant", "frozen", "closed"]
    branch_name: str = Field(description="Branch name")
    ifsc_code: str = Field(description="IFSC code")


class Transaction(BaseModel):
    """Individual transaction record."""

    model_config = ConfigDict(strict=True)

    transaction_id: str = Field(description="Unique transaction reference")
    date: datetime = Field(description="Transaction date and time")
    description: str = Field(description="Transaction narration/description")
    amount: Decimal = Field(description="Transaction amount")
    type: Literal["credit", "debit"] = Field(description="Transaction type")
    balance_after: Decimal = Field(description="Balance after transaction")
    channel: Literal["ATM", "UPI", "NEFT", "RTGS", "IMPS", "POS", "ONLINE", "BRANCH"]
    counterparty: str | None = Field(default=None, description="Payee/Payer name if available")


class ServiceRequest(BaseModel):
    """Customer service request status."""

    model_config = ConfigDict(strict=True)

    request_id: str = Field(description="Service request ID")
    type: Literal[
        "cheque_book",
        "address_change",
        "kyc_update",
        "card_block",
        "credit_limit_increase",
        "statement_request",
    ]
    status: Literal["submitted", "processing", "completed", "rejected"]
    submitted_at: datetime = Field(description="Submission timestamp")
    estimated_completion: datetime | None = Field(default=None, description="Estimated completion")
    notes: str | None = Field(default=None, description="Additional notes")
