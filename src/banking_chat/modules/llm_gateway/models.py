"""SQLAlchemy ORM models for the LLM gateway cost tracking.

Rates are stored per-provider/per-model so new models can be priced at runtime
without code changes. Every LLM call is persisted as a ``LLMCostRecord`` for
auditing, budget analytics, and cost dashboards.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from banking_chat.core.db.base import Base


class LLMCostRate(Base):
    """Runtime-configurable pricing per provider and model (USD per 1K tokens)."""

    __tablename__ = "llm_cost_rates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    input_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    output_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (
        UniqueConstraint("provider", "model", name="uq_llm_cost_rate_provider_model"),
        Index("idx_llm_cost_rate_lookup", "provider", "model"),
    )


class LLMCostRecord(Base):
    """Audit record of a single LLM invocation: tokens, cost, and routing context."""

    __tablename__ = "llm_cost_records"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    customer_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    total_tokens: Mapped[int] = mapped_column(nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False, index=True
    )

    __table_args__ = (Index("idx_llm_cost_record_customer_time", "customer_id", "created_at"),)
