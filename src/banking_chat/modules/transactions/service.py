"""Transactions domain service handling transaction queries and aggregations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from banking_chat.core.common.types import Transaction
from banking_chat.modules.transactions.models import TransactionModel
from banking_chat.modules.transactions.schemas import (
    SpendingSummaryResponse,
    TransactionListResponse,
    TransactionQueryRequest,
)


class TransactionsService:
    """Service layer for transaction operations."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db = db_session

    async def get_transactions(
        self, customer_id: str, query: TransactionQueryRequest | None = None
    ) -> TransactionListResponse:
        """Fetch transactions for a given customer."""
        req = query or TransactionQueryRequest()

        if self.db is not None:
            stmt = (
                select(TransactionModel)
                .where(TransactionModel.customer_id == customer_id)
                .order_by(desc(TransactionModel.date))
                .limit(req.limit)
            )
            if req.account_number:
                stmt = stmt.where(TransactionModel.account_number.endswith(req.account_number[-4:]))
            if req.transaction_type in ("credit", "debit"):
                stmt = stmt.where(TransactionModel.type == req.transaction_type)
            if req.start_date:
                stmt = stmt.where(TransactionModel.date >= req.start_date)
            if req.end_date:
                stmt = stmt.where(TransactionModel.date <= req.end_date)

            result = await self.db.execute(stmt)
            records = result.scalars().all()
            transactions = [
                Transaction(
                    transaction_id=m.transaction_id,
                    customer_id=m.customer_id,
                    date=m.date,
                    description=m.description,
                    amount=m.amount,
                    type=m.type,
                    balance_after=m.balance_after,
                    channel=m.channel,
                    counterparty=m.counterparty,
                )
                for m in records
            ]
        else:
            # Fallback mock data
            now = datetime.now(UTC)
            transactions = [
                Transaction(
                    transaction_id="TXN987654321",
                    date=now - timedelta(days=1),
                    description="UPI/Amazon India/Payment",
                    amount=Decimal("1499.00"),
                    type="debit",
                    balance_after=Decimal("123931.50"),
                    channel="UPI",
                    counterparty="Amazon India",
                ),
                Transaction(
                    transaction_id="TXN987654320",
                    date=now - timedelta(days=3),
                    description="Salary Credit - TechCorp Ltd",
                    amount=Decimal("85000.00"),
                    type="credit",
                    balance_after=Decimal("125430.50"),
                    channel="NEFT",
                    counterparty="TechCorp Ltd",
                ),
                Transaction(
                    transaction_id="TXN987654319",
                    date=now - timedelta(days=5),
                    description="ATM Cash Withdrawal",
                    amount=Decimal("5000.00"),
                    type="debit",
                    balance_after=Decimal("40430.50"),
                    channel="ATM",
                    counterparty=None,
                ),
            ]

        return TransactionListResponse(
            customer_id=customer_id,
            transactions=transactions,
            total_count=len(transactions),
        )

    async def get_spending_summary(self, customer_id: str, days: int = 30) -> SpendingSummaryResponse:
        """Calculate spending summary for customer over the specified time window."""
        start_date = datetime.now(UTC) - timedelta(days=days)
        req = TransactionQueryRequest(limit=100, start_date=start_date)
        txns = await self.get_transactions(customer_id, req)

        total_spent = Decimal("0.00")
        total_received = Decimal("0.00")
        categories: dict[str, Decimal] = {}

        for t in txns.transactions:
            if t.type == "debit":
                total_spent += t.amount
                cat = "Shopping" if "amazon" in t.description.lower() else "Cash/Other"
                categories[cat] = categories.get(cat, Decimal("0.00")) + t.amount
            elif t.type == "credit":
                total_received += t.amount

        net_flow = total_received - total_spent

        return SpendingSummaryResponse(
            customer_id=customer_id,
            total_spent=total_spent,
            total_received=total_received,
            net_flow=net_flow,
            top_categories=categories,
        )
