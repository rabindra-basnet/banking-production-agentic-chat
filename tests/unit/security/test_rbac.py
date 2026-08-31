"""Unit tests for RBAC checker and policies."""

from __future__ import annotations

import pytest

from banking_chat.core.common.exceptions import AuthorizationError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.modules.auth.rbac import RBACChecker


def test_rbac_tier_permission_allowed(premium_user: AuthenticatedUser) -> None:
    RBACChecker.check_tier_permission(premium_user, CustomerTier.STANDARD)
    RBACChecker.check_tier_permission(premium_user, CustomerTier.PREMIUM)


def test_rbac_tier_permission_denied(standard_user: AuthenticatedUser) -> None:
    with pytest.raises(AuthorizationError):
        RBACChecker.check_tier_permission(standard_user, CustomerTier.PRIVILEGED)


def test_rbac_account_access(standard_user: AuthenticatedUser) -> None:
    RBACChecker.check_account_access(standard_user, "XXXXXXXXXXXX1234")

    with pytest.raises(AuthorizationError):
        RBACChecker.check_account_access(standard_user, "XXXXXXXXXXXX9999")
