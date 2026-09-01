"""Seed script to populate SQLite/PostgreSQL database with dummy banking data."""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from banking_chat.core.config.settings import get_settings
from banking_chat.core.db.base import Base
from banking_chat.modules.accounts.models import BankAccountModel
from banking_chat.modules.services.models import ServiceRequestModel
from banking_chat.modules.transactions.models import TransactionModel


async def seed_database(seed_file_path: str | Path | None = None) -> None:
    """Read JSON seed file and insert records into database."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    data_path = Path(seed_file_path or "data/seed_banking_data.json")
    if not data_path.exists():
        print(f"Seed file not found at {data_path}")
        return

    with open(data_path, encoding="utf-8") as f:
        customers_data = json.load(f)

    async with session_factory() as session:
        for cust in customers_data:
            cust_id = cust["customer_id"]

            # 1. Accounts
            for acc in cust.get("accounts", []):
                stmt = select(BankAccountModel).where(
                    BankAccountModel.account_number == acc["account_number"]
                )
                existing = (await session.execute(stmt)).scalars().first()
                if not existing:
                    account_model = BankAccountModel(
                        id=uuid4(),
                        customer_id=cust_id,
                        account_number=acc["account_number"],
                        account_type=acc["account_type"],
                        balance=Decimal(str(acc["balance"])),
                        currency=acc.get("currency", "INR"),
                        status=acc.get("status", "active"),
                        branch_name=acc.get("branch_name", "Main Branch"),
                        ifsc_code=acc.get("ifsc_code", "BANK0000001"),
                    )
                    session.add(account_model)

            # 2. Transactions
            for txn in cust.get("transactions", []):
                stmt = select(TransactionModel).where(
                    TransactionModel.transaction_id == txn["transaction_id"]
                )
                existing = (await session.execute(stmt)).scalars().first()
                if not existing:
                    txn_dt = datetime.fromisoformat(txn["date"].replace("Z", "+00:00"))
                    txn_model = TransactionModel(
                        id=uuid4(),
                        transaction_id=txn["transaction_id"],
                        account_number=txn["account_number"],
                        customer_id=cust_id,
                        date=txn_dt,
                        description=txn["description"],
                        amount=Decimal(str(txn["amount"])),
                        type=txn["type"],
                        balance_after=Decimal(str(txn["balance_after"])),
                        channel=txn.get("channel", "UPI"),
                        counterparty=txn.get("counterparty"),
                    )
                    session.add(txn_model)

            # 3. Service Requests
            for srv in cust.get("service_requests", []):
                stmt = select(ServiceRequestModel).where(
                    ServiceRequestModel.request_id == srv["request_id"]
                )
                existing = (await session.execute(stmt)).scalars().first()
                if not existing:
                    sub_dt = datetime.fromisoformat(srv["submitted_at"].replace("Z", "+00:00"))
                    est_dt = (
                        datetime.fromisoformat(srv["estimated_completion"].replace("Z", "+00:00"))
                        if srv.get("estimated_completion")
                        else None
                    )
                    srv_model = ServiceRequestModel(
                        id=uuid4(),
                        request_id=srv["request_id"],
                        customer_id=cust_id,
                        type=srv["type"],
                        status=srv.get("status", "submitted"),
                        submitted_at=sub_dt,
                        estimated_completion=est_dt,
                        notes=srv.get("notes"),
                    )
                    session.add(srv_model)

        await session.commit()
        print(f"✅ Database successfully seeded from {data_path}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
