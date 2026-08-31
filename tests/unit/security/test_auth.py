"""Unit tests for JWT authentication, access tokens, and refresh token rotation."""

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


def test_jwt_token_pair_and_refresh() -> None:
    validator = JWTValidator(secret_key="test-secret-key-12345678901234567890", algorithm="HS256")
    pair = validator.create_token_pair(
        customer_id="CIF123456",
        name="Ananya Roy",
        email="ananya.roy@example.com",
        tier=CustomerTier.PRIVILEGED,
    )

    assert "access_token" in pair
    assert "refresh_token" in pair
    assert pair["token_type"] == "Bearer"
    assert isinstance(pair["access_token"], str)
    assert isinstance(pair["refresh_token"], str)

    # Validate access token
    user = validator.validate_token(pair["access_token"])
    assert user.customer_id == "CIF123456"
    assert user.tier == CustomerTier.PRIVILEGED

    # Refresh access token with refresh token
    new_pair = validator.refresh_access_token(pair["refresh_token"])
    assert "access_token" in new_pair
    assert "refresh_token" in new_pair
    assert new_pair["access_token"] != pair["access_token"]


def test_jwt_validator_invalid_token() -> None:
    validator = JWTValidator(secret_key="test-secret-key-12345678901234567890", algorithm="HS256")
    with pytest.raises(AuthenticationError):
        validator.validate_token("invalid.token.structure")


def test_jwt_refresh_with_access_token_fails() -> None:
    validator = JWTValidator(secret_key="test-secret-key-12345678901234567890", algorithm="HS256")
    pair = validator.create_token_pair(customer_id="CIF123456")
    # Passing access token to refresh endpoint must raise AuthenticationError
    with pytest.raises(AuthenticationError, match="Refresh token required"):
        validator.refresh_access_token(str(pair["access_token"]))
