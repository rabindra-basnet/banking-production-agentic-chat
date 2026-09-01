"""Shared type definitions and data models used across the application."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ─── Base Pydantic Model with Strict Validation & Coercion Safeguards ───


class StrictBaseModel(BaseModel):
    """Base Pydantic model enforcing strict type validation while allowing standard JSON string coercion."""

    model_config = ConfigDict(strict=False, validate_assignment=True, extra="forbid")


class StrictFrozenBaseModel(BaseModel):
    """Immutable base Pydantic model enforcing strict type validation."""

    model_config = ConfigDict(strict=False, frozen=True, validate_assignment=True, extra="forbid")


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


class AuthenticatedUser(StrictFrozenBaseModel):
    """Validated user identity from the bank's identity provider (IdP)."""

    user_id: UUID = Field(description="Unique customer identifier from bank's IdP")
    customer_id: str = Field(description="Bank's internal customer number (CIF)")
    name: str = Field(description="Customer's display name")
    email: str = Field(description="Verified email address")
    tier: CustomerTier = Field(description="Authorization tier")
    accounts: list[str] = Field(description="List of account numbers the customer owns")
    session_id: UUID = Field(description="Current chat session ID")
    token_expiry: datetime = Field(description="JWT token expiration timestamp")


# ─── Banking Entity Models ───


class BankAccount(StrictBaseModel):
    """Bank account details returned by Accounts MCP Server."""

    account_number: str = Field(description="Masked account number (last 4 digits visible)")
    account_type: Literal["savings", "current", "fixed_deposit", "recurring_deposit"]
    balance: Decimal = Field(description="Current available balance")
    currency: str = Field(default="NPR", description="Currency code (ISO 4217, default NPR)")
    status: Literal["active", "dormant", "frozen", "closed"]
    branch_name: str = Field(description="Branch name")
    ifsc_code: str = Field(default="NIBL0000001", description="Branch routing / Swift / IFSC code")


class Transaction(StrictBaseModel):
    """Individual transaction record."""

    transaction_id: str = Field(description="Unique transaction reference")
    customer_id: str | None = Field(default=None, description="Customer CIF who performed/owns the transaction")
    date: datetime = Field(description="Transaction date and time")
    description: str = Field(description="Transaction narration/description")
    amount: Decimal = Field(description="Transaction amount")
    type: Literal["credit", "debit"] = Field(description="Transaction type")
    balance_after: Decimal = Field(description="Balance after transaction")
    channel: Literal["ATM", "FONEPAY", "CONNECTIPS", "NPI", "ESPEWA", "KHALTI", "POS", "ONLINE", "BRANCH", "UPI", "NEFT", "RTGS", "IMPS"]
    counterparty: str | None = Field(default=None, description="Payee/Payer name if available")


class ServiceRequest(StrictBaseModel):
    """Customer service request status."""

    request_id: str = Field(description="Service request ID")
    type: Literal[
        "cheque_book",
        "address_change",
        "kyc_update",
        "card_block",
        "credit_limit_increase",
        "statement_request",
    ] = Field(description="Type of service request")
    status: Literal["submitted", "processing", "completed", "rejected"] = Field(
        default="submitted", description="Request lifecycle status"
    )
    submitted_at: datetime = Field(description="Submission timestamp")
    estimated_completion: datetime | None = Field(default=None, description="Estimated completion timestamp")
    notes: str | None = Field(default=None, description="Additional notes")


class Customer(StrictBaseModel):
    """Customer entity representation."""

    customer_id: str = Field(description="Customer CIF number")
    name: str = Field(description="Full name")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer tier")
    accounts: list[BankAccount] = Field(default_factory=list, description="Linked accounts")
    created_at: datetime = Field(description="Account creation timestamp")
