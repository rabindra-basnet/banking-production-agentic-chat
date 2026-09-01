"""Seed script to populate SQLite/PostgreSQL database with dummy banking data and registered users."""

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
from banking_chat.modules.auth.models import Role, UserModel
from banking_chat.modules.services.models import ServiceRequestModel
from banking_chat.modules.transactions.models import TransactionModel

# Default Registered Banking Users
SEED_USERS = [
    {
        "customer_id": "CIF908123",
        "name": "Rabindra Basnet",
        "email": "rabindra.basnet@example.com.np",
        "role": "customer",
        "tier": "standard",
        "accounts_json": json.dumps(["0120100056781234 (Savings Khata)", "0120100056785678 (Muddati Khata)"]),
        "password_hash": "password123",
    },
    {
        "customer_id": "CIF908456",
        "name": "Sita Shrestha",
        "email": "sita.shrestha@example.com.np",
        "role": "customer",
        "tier": "premium",
        "accounts_json": json.dumps(["0240100088994433 (Savings Khata)", "0240100088997788 (Current Khata)"]),
        "password_hash": "password123",
    },
    {
        "customer_id": "CIF908999",
        "name": "Prashant Thapa",
        "email": "prashant.thapa@example.com.np",
        "role": "admin",
        "tier": "privileged",
        "accounts_json": json.dumps(["0380100077771122 (Corporate Savings)", "0380100077773344 (Muddati Khata)"]),
        "password_hash": "password123",
    },
]


async def seed_database(seed_file_path: str | Path | None = None) -> None:
    """Read JSON seed file and insert records into database."""
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    data_path = Path(seed_file_path or "data/seed_banking_data.json")
    customers_data = []
    if data_path.exists():
        with open(data_path, encoding="utf-8") as f:
            customers_data = json.load(f)

    async with session_factory() as session:
        # 1. Seed Users table
        for u in SEED_USERS:
            stmt = select(UserModel).where(UserModel.customer_id == u["customer_id"])
            existing = (await session.execute(stmt)).scalars().first()
            if not existing:
                user_model = UserModel(
                    id=uuid4(),
                    customer_id=u["customer_id"],
                    name=u["name"],
                    email=u["email"],
                    role=u["role"],
                    tier=u["tier"],
                    accounts_json=u["accounts_json"],
                    password_hash=u["password_hash"],
                )
                session.add(user_model)

        # 2. Seed Accounts, Transactions, Service Requests
        for cust in customers_data:
            cust_id = cust["customer_id"]

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
                        currency=acc.get("currency", "NPR"),
                        status=acc.get("status", "active"),
                        branch_name=acc.get("branch_name", "Main Branch"),
                        ifsc_code=acc.get("ifsc_code", "BANK0000001"),
                    )
                    session.add(account_model)

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
        print("✅ Database successfully seeded with registered users and banking records")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_database())
