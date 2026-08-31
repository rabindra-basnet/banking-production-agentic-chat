"""SQLAlchemy ORM model for transactions."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from banking_chat.core.db.base import Base


class TransactionModel(Base):
    """SQLAlchemy model representing a banking transaction."""

    __tablename__ = "transactions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False, default=lambda: datetime.now(UTC)
    )
    description: Mapped[str] = mapped_column(String(256), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    type: Mapped[str] = mapped_column(String(10), nullable=False)  # credit / debit
    balance_after: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="UPI")
    counterparty: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
