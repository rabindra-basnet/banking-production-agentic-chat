"""Authentication and Authorization data models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from banking_chat.core.common.types import CustomerTier, StrictBaseModel, StrictFrozenBaseModel


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


class RefreshTokenRequest(StrictBaseModel):
    """Payload to refresh an access token."""

    refresh_token: str = Field(description="Valid long-lived refresh token")


class TokenResponse(StrictBaseModel):
    """Token response payload containing access and refresh token pair."""

    access_token: str = Field(description="Short-lived access token")
    refresh_token: str = Field(description="Long-lived refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(description="Access token lifespan in seconds")


class AuthContext(StrictFrozenBaseModel):
    """Contextual authorization information attached to request state."""

    user_id: UUID
    customer_id: str
    name: str
    email: str
    tier: CustomerTier
    accounts: list[str]
    session_id: UUID
    permissions: frozenset[str] = frozenset()
