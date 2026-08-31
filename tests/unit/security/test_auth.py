"""Unit tests for JWT authentication and token validation."""

from __future__ import annotations

import pytest

from banking_chat.core.common.exceptions import AuthenticationError
from banking_chat.core.common.types import CustomerTier
from banking_chat.modules.auth.jwt_validator import JWTValidator


def test_jwt_validator_create_and_validate() -> None:
    validator = JWTValidator(secret_key="test-secret-key-12345678901234567890", algorithm="HS256")
    token = validator.create_mock_token(
        customer_id="CIF999888",
        name="Test User",
        email="test@example.com",
        tier=CustomerTier.PREMIUM,
    )
    assert isinstance(token, str)

    user = validator.validate_token(token)
    assert user.customer_id == "CIF999888"
    assert user.name == "Test User"
    assert user.tier == CustomerTier.PREMIUM


def test_jwt_validator_invalid_token() -> None:
    validator = JWTValidator(secret_key="test-secret-key-12345678901234567890", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        validator.validate_token("invalid.token.structure")
