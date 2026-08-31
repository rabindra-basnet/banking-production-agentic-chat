"""Shared test fixtures for the banking chat test suite."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from banking_chat.core.common.types import AuthenticatedUser, CustomerTier


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
