"""SQLAlchemy ORM model for bank accounts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from banking_chat.core.db.base import Base


class BankAccountModel(Base):
    """SQLAlchemy model representing a customer's bank account."""

    __tablename__ = "bank_accounts"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    account_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, default="savings")
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    branch_name: Mapped[str] = mapped_column(String(128), nullable=False, default="Main Branch")
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False, default="BANK0000001")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
