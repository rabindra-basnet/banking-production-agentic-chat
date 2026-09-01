"""Authentication, User Database ORM Entities, and Pydantic Schemas."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, TypedDict
from uuid import UUID, uuid4

from pydantic import Field
from sqlalchemy import DateTime, Index, JSON, String, select
from sqlalchemy.orm import Mapped, mapped_column

from banking_chat.core.common.types import CustomerTier, StrictBaseModel, StrictFrozenBaseModel
from banking_chat.core.db.base import Base
from banking_chat.core.db.session import get_session_factory


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


# ─── SQLAlchemy Database ORM Entity for Users ───

class UserModel(Base):
    """SQLAlchemy model representing authenticated customers and administrators in the database."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    customer_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=Role.CUSTOMER, nullable=False)
    tier: Mapped[str] = mapped_column(String(32), default=CustomerTier.STANDARD, nullable=False)
    accounts_json: Mapped[str] = mapped_column(String(512), default="[]", nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        Index("idx_users_email_role", "email", "role"),
    )


class UserProfileSchema(StrictBaseModel):
    """Customer / User registry schema for system authentication."""

    customer_id: str = Field(description="Unique Customer Identifier / CIF")
    name: str = Field(description="Customer Full Name")
    email: str = Field(description="Email address")
    role: Role = Field(default=Role.CUSTOMER, description="User authorization role (customer, support_agent, admin)")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer classification tier")
    accounts: list[str] = Field(default_factory=list, description="Authorized account numbers with types")
    password: str = Field(default="password123", description="Hashed / authentication password")


class UserRepository:
    """Database repository for user authentication and customer lookups."""

    @staticmethod
    async def get_by_customer_id(customer_id: str) -> UserProfileSchema | None:
        """Fetch user profile from database by customer ID (CIF)."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(UserModel).where(UserModel.customer_id == customer_id)
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None

            try:
                accounts = json.loads(user_orm.accounts_json)
            except Exception:
                accounts = []

            return UserProfileSchema(
                customer_id=user_orm.customer_id,
                name=user_orm.name,
                email=user_orm.email,
                role=Role(user_orm.role),
                tier=CustomerTier(user_orm.tier),
                accounts=accounts,
                password=user_orm.password_hash,
            )

    @staticmethod
    async def get_by_identifier_or_email(identifier: str) -> UserProfileSchema | None:
        """Fetch user profile from database by CIF, Email, or Full Name."""
        factory = get_session_factory()
        async with factory() as session:
            stmt = select(UserModel).where(
                (UserModel.customer_id == identifier) | (UserModel.email == identifier) | (UserModel.name == identifier)
            )
            result = await session.execute(stmt)
            user_orm = result.scalar_one_or_none()
            if not user_orm:
                return None

            try:
                accounts = json.loads(user_orm.accounts_json)
            except Exception:
                accounts = []

            return UserProfileSchema(
                customer_id=user_orm.customer_id,
                name=user_orm.name,
                email=user_orm.email,
                role=Role(user_orm.role),
                tier=CustomerTier(user_orm.tier),
                accounts=accounts,
                password=user_orm.password_hash,
            )


class AuthContext(StrictBaseModel):
    """Security and authorization context of the authenticated caller."""

    customer_id: str = Field(description="Unique Customer Identifier / CIF")
    roles: list[Role] = Field(default_factory=lambda: [Role.CUSTOMER], description="Assigned authorization roles")
    permissions: list[Permission] = Field(default_factory=list, description="Computed caller permissions")
    tier: CustomerTier = Field(default=CustomerTier.STANDARD, description="Customer classification tier")


class TokenPayload(StrictFrozenBaseModel):
    """Decoded JWT payload representation."""

    sub: UUID | str = Field(description="Subject identifier (internal user UUID)")
    cif: str = Field(description="Customer Identifier / CIF number")
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


class RefreshResponse(StrictBaseModel):
    """Standard OAuth2/OIDC refresh response returning strictly access token and expiration."""

    access_token: str = Field(description="Short-lived JWT access token stored in JS client memory")
    token_type: str = Field(default="Bearer", description="OAuth2 token type")
    expires_in: int = Field(default=900, description="Access token expiration window in seconds")


class UserProfileResponse(StrictBaseModel):
    """User profile and banking account details returned by /auth/me."""

    customer_id: str = Field(default="CIF908123", description="Authenticated Customer ID")
    name: str = Field(default="Customer", description="Full Name")
    email: str = Field(default="", description="Email address")
    role: str = Field(default="customer", description="Authorization role: customer | support_agent | admin")
    tier: str = Field(default="standard", description="Customer Tier")
    accounts: list[str] = Field(default_factory=list, description="Associated Bank Accounts")


class TokenResponse(StrictBaseModel):
    """SSO Login response payload containing access token and basic user info."""

    access_token: str = Field(default="", description="Short-lived JWT access token stored in JS client memory")
    csrf_token: str = Field(default="", description="Anti-CSRF token")
    customer_id: str = Field(default="CIF908123", description="Authenticated Customer ID")
    name: str = Field(default="Customer", description="Full Name")
    email: str = Field(default="", description="Email address")
    role: str = Field(default="customer", description="Authorization role: customer | support_agent | admin")
    tier: str = Field(default="standard", description="Customer Tier")
    accounts: list[str] = Field(default_factory=list, description="Associated Bank Accounts")
