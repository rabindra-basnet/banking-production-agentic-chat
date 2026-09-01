"""Database-backed persistent token blacklist manager for audit-compliant token revocations."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column

from banking_chat.core.db.base import Base
from banking_chat.core.db.session import get_session_factory

logger = logging.getLogger("banking_chat.security.blacklist")


class RevokedToken(Base):
    """Database table recording permanently revoked / blacklisted access and refresh tokens."""

    __tablename__ = "revoked_tokens"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    token_type: Mapped[str] = mapped_column(String(20), default="refresh", nullable=False)
    customer_id: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    __table_args__ = (
        Index("idx_revoked_token_hash_exp", "token_hash", "expires_at"),
    )


class TokenBlacklistManager:
    """Manages persistent token revocations written directly to PostgreSQL / SQLite database."""

    _memory_cache: set[str] = set()

    @staticmethod
    def hash_token(token: str) -> str:
        """Create SHA-256 fingerprint hash of the token for secure, indexed database storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    async def blacklist_token(
        self,
        token: str,
        token_type: str = "refresh",
        customer_id: str | None = None,
        expiry_seconds: int = 7 * 86400,
    ) -> None:
        """Permanently record a revoked token in the database table with expiration timestamp."""
        token_hash = self.hash_token(token)
        self._memory_cache.add(token_hash)

        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=expiry_seconds)

        try:
            factory = get_session_factory()
            async with factory() as session:
                revocation_record = RevokedToken(
                    token_hash=token_hash,
                    token_type=token_type,
                    customer_id=customer_id,
                    revoked_at=now,
                    expires_at=expires_at,
                )
                session.add(revocation_record)
                await session.commit()
                logger.info(
                    "Token blacklisted and committed to database",
                    extra={"token_hash": token_hash[:12], "customer_id": customer_id, "token_type": token_type},
                )
        except IntegrityError:
            pass
        except Exception as err:
            logger.warning(
                "Could not persist token revocation to database: %s",
                err,
                extra={"token_hash": token_hash[:12]},
            )

    async def is_blacklisted(self, token: str) -> bool:
        """Check if a token has been revoked in database or cache."""
        token_hash = self.hash_token(token)

        if token_hash in self._memory_cache:
            return True

        try:
            factory = get_session_factory()
            async with factory() as session:
                now = datetime.now(UTC)
                stmt = select(RevokedToken).where(
                    RevokedToken.token_hash == token_hash,
                    RevokedToken.expires_at > now,
                )
                result = await session.execute(stmt)
                record = result.scalars().first()
                if record is not None:
                    self._memory_cache.add(token_hash)
                    return True
        except Exception as err:
            logger.error("Error querying token blacklist from database: %s", err)

        return False

    def is_blacklisted_sync(self, token: str) -> bool:
        """Synchronous check using in-memory cached database hashes."""
        token_hash = self.hash_token(token)
        return token_hash in self._memory_cache
