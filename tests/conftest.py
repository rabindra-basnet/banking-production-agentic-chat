"""Shared test fixtures for the banking chat test suite."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from uuid import uuid4

import pytest

from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.db.base import Base
from banking_chat.core.db.session import get_engine, get_session_factory
from banking_chat.modules.auth.models import Role, UserModel


@pytest.fixture
def standard_user() -> AuthenticatedUser:
    """Create a standard tier test user."""
    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF001234",
        name="Rajesh Kumar",
        email="rajesh.kumar@example.com",
        tier=CustomerTier.STANDARD,
        accounts=["XXXXXXXXXXXX1234", "XXXXXXXXXXXX5678"],
        session_id=uuid4(),
        token_expiry=datetime(2026, 12, 31, tzinfo=UTC),
    )


@pytest.fixture
def premium_user() -> AuthenticatedUser:
    """Create a premium tier test user."""
    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF005678",
        name="Priya Sharma",
        email="priya.sharma@example.com",
        tier=CustomerTier.PREMIUM,
        accounts=["XXXXXXXXXXXX9012"],
        session_id=uuid4(),
        token_expiry=datetime(2026, 12, 31, tzinfo=UTC),
    )


@pytest.fixture
def privileged_user() -> AuthenticatedUser:
    """Create a privileged tier test user."""
    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF009999",
        name="Amit Patel",
        email="amit.patel@example.com",
        tier=CustomerTier.PRIVILEGED,
        accounts=["XXXXXXXXXXXX3456", "XXXXXXXXXXXX7890", "XXXXXXXXXXXX2345"],
        session_id=uuid4(),
        token_expiry=datetime(2026, 12, 31, tzinfo=UTC),
    )


def _seed_test_users() -> None:
    """Create database schema and seed the auth test users from seed_banking_data.json."""
    engine = get_engine()

    async def _setup() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        seed_file = Path(__file__).resolve().parent.parent / "data" / "seed_banking_data.json"
        if not seed_file.exists():
            return

        with open(seed_file, encoding="utf-8") as f:
            customers = json.load(f)

        factory = get_session_factory()
        async with factory() as session:
            hashed = sha256(b"password123").hexdigest()
            for cust in customers:
                accounts = [
                    f"{acc['account_number']} ({acc['account_type'].replace('_', ' ').title()} Khata)"
                    for acc in cust.get("accounts", [])
                ]
                user = UserModel(
                    id=uuid4(),
                    customer_id=cust["customer_id"],
                    name=cust.get("name", "Customer"),
                    email=cust.get("email", f"{cust['customer_id']}@example.com"),
                    role=Role.CUSTOMER,
                    tier=cust.get("tier", CustomerTier.STANDARD),
                    accounts_json=json.dumps(accounts),
                    password_hash=hashed,
                )
                session.add(user)
            await session.commit()

    import asyncio

    asyncio.run(_setup())


@pytest.fixture(autouse=True, scope="session")
def _seed_database() -> None:
    """Autouse session-scoped fixture ensuring test DB schema and users exist."""
    _seed_test_users()
