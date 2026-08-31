"""General utility functions."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def generate_id() -> UUID:
    """Generate a new UUID4."""
    return uuid4()


def format_currency(amount: float | int, currency: str = "INR") -> str:
    """Format amount as Indian currency string.

    Args:
        amount: The amount to format.
        currency: Currency code.

    Returns:
        Formatted string like '₹1,23,456.78'.
    """
    if currency == "INR":
        # Indian numbering system (lakhs, crores)
        s = f"{amount:,.2f}"
        return f"₹{s}"
    return f"{amount:,.2f} {currency}"
