"""Tests for authentication bypass attempts."""

from __future__ import annotations

import pytest

from banking_chat.core.common.exceptions import AuthenticationError
from banking_chat.modules.auth.jwt_validator import JWTValidator


def test_forged_token_rejected() -> None:
    validator = JWTValidator(secret_key="real-secret-key-12345678901234567890", algorithm="HS256")
    attacker_validator = JWTValidator(secret_key="attacker-secret-key-wrong", algorithm="HS256")
    forged_token = attacker_validator.create_mock_token(customer_id="CIF009999")

    with pytest.raises(AuthenticationError):
        validator.validate_token(forged_token)
