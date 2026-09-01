"""General utility functions for Nepali and global banking contexts."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


def generate_id() -> UUID:
    """Generate a new UUID4."""
    return uuid4()


def format_currency(amount: float | int | Decimal, currency: str = "NPR") -> str:
    """Format amount as Nepali / South Asian currency string (Lakhs & Crores).

    Args:
        amount: The amount to format.
        currency: Currency code (default NPR).

    Returns:
        Formatted string like 'Rs. 1,23,456.78' or 'NPR 1,23,456.78'.
    """
    s = f"{amount:,.2f}"
    if currency in ("NPR", "NEPALI_RUPEE"):
        return f"Rs. {s}"
    if currency == "INR":
        return f"₹{s}"
    return f"{currency} {s}"
