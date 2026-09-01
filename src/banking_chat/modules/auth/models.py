"""Authentication and Authorization data models and User Directory Schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from typing import TypedDict

from pydantic import Field

from banking_chat.core.common.types import CustomerTier, StrictBaseModel, StrictFrozenBaseModel


class TokenPairDict(TypedDict):
    """Strongly typed dictionary for JWT access & refresh token pairs."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    cif: str


class Role(StrEnum):
    """User authorization roles."""

    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    ADMIN = "admin"


class Permission(StrEnum):
    """Fine-grained access control permissions."""

    VIEW_ACCOUNTS = "accounts:read"
    VIEW_TRANSACTIONS = "transactions:read"
    CREATE_SERVICE_REQUEST = "services:create"
    BLOCK_CARD = "services:block_card"
    ADMIN_CONFIG = "admin:config"


class UserProfileSchema(StrictBaseModel):
    """Customer / User registry schema for system authentication."""

    customer_id: str = Field(description="Unique Customer Identifier / CIF")
    name: str = Field(description="Customer Full Name")
    email: str = Field(description="Email address")
    role: Role = Field(default=Role.CUSTOMER, description="User authorization role (customer, support_agent, admin)")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer classification tier")
    accounts: list[str] = Field(default_factory=list, description="Authorized account numbers with types")
    password: str = Field(default="password123", description="Hashed / authentication password")


class AuthContext(StrictBaseModel):
    """Security and authorization context of the authenticated caller."""

    customer_id: str = Field(description="Unique Customer Identifier / CIF")
    roles: list[Role] = Field(default_factory=lambda: [Role.CUSTOMER], description="Assigned authorization roles")
    permissions: list[Permission] = Field(default_factory=list, description="Computed granular permissions")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer classification tier")


class TokenPayload(StrictBaseModel):
    """Decoded JWT payload from Identity Provider."""

    sub: str = Field(description="Subject (User ID)")
    cif: str = Field(description="Customer Information File number")
    name: str = Field(description="Display Name")
    email: str = Field(description="Email address")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer tier")
    accounts: list[str] = Field(default_factory=list, description="Authorized account numbers")
    roles: list[str] = Field(default_factory=lambda: [str(Role.CUSTOMER)], description="Assigned roles")
    token_type: str = Field(default="access", description="Type of token: access | refresh")
    exp: int | datetime = Field(description="Expiration timestamp")
    iat: int | datetime = Field(description="Issued at timestamp")
    iss: str = Field(description="Issuer URL")
    aud: str = Field(description="Audience")


class LoginRequest(StrictBaseModel):
    """Real system SSO / Banking Login payload."""

    username: str = Field(description="Customer Identifier, Email, or Mobile number (e.g. CIF908123 or rabindra.basnet@example.com.np)")
    password: str = Field(description="Password or Auth Credential")


class RefreshTokenRequest(StrictBaseModel):
    """Payload to refresh an access token (optional if sent via httpOnly cookie)."""

    refresh_token: str | None = Field(default=None, description="Optional refresh token if not in cookies")


class TokenResponse(StrictBaseModel):
    """Token response payload returned to client (access token returned in-memory, refresh token in HttpOnly cookie)."""

    access_token: str = Field(default="", description="Short-lived JWT access token stored in JS client memory")
    csrf_token: str = Field(default="", description="Anti-CSRF token")
    customer_id: str = Field(default="CIF908123", description="Authenticated Customer ID")
    name: str = Field(default="Customer", description="Full Name")
    email: str = Field(default="", description="Email address")
    role: str = Field(default="customer", description="Authorization role: customer | support_agent | admin")
    tier: str = Field(default="standard", description="Customer Tier")
    accounts: list[str] = Field(default_factory=list, description="Associated Bank Accounts")
