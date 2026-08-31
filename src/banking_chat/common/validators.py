"""Common validators for input sanitization and validation."""

from __future__ import annotations

import re


def sanitize_user_input(text: str, max_length: int = 2000) -> str:
    """Sanitize user input by removing control characters and limiting length.

    Args:
        text: Raw user input.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    # Remove control characters except newlines and tabs
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return cleaned[:max_length].strip()


def is_valid_account_number(account_number: str) -> bool:
    """Validate Indian bank account number format (9-18 digits)."""
    return bool(re.match(r"^\d{9,18}$", account_number))


def mask_account_number(account_number: str) -> str:
    """Mask account number showing only last 4 digits."""
    if len(account_number) <= 4:
        return account_number
    return "X" * (len(account_number) - 4) + account_number[-4:]


def is_valid_ifsc(ifsc: str) -> bool:
    """Validate IFSC code format."""
    return bool(re.match(r"^[A-Z]{4}0[A-Z0-9]{6}$", ifsc))
