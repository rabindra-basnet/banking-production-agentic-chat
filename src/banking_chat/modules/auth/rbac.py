"""Role-Based Access Control and Tier policy verification."""

from __future__ import annotations

from banking_chat.core.common.exceptions import AuthorizationError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier


class RBACChecker:
    """Evaluates user permissions based on customer tier and ownership."""

    TIER_RANK: dict[CustomerTier, int] = {
        CustomerTier.STANDARD: 1,
        CustomerTier.PREMIUM: 2,
        CustomerTier.PRIVILEGED: 3,
    }

    @classmethod
    def check_tier_permission(cls, user: AuthenticatedUser, minimum_tier: CustomerTier) -> None:
        """Check if user meets the minimum customer tier requirement."""
        user_rank = cls.TIER_RANK.get(user.tier, 0)
        required_rank = cls.TIER_RANK.get(minimum_tier, 0)
        if user_rank < required_rank:
            raise AuthorizationError(
                f"Feature requires {minimum_tier} tier, user is {user.tier}",
                required_tier=str(minimum_tier),
            )

    @classmethod
    def check_account_access(cls, user: AuthenticatedUser, account_number: str) -> None:
        """Verify that the user is authorized to access the specified account."""
        clean_target = account_number[-4:]
        is_owner = any(acc.endswith(clean_target) for acc in user.accounts)
        if not is_owner:
            raise AuthorizationError(f"User does not have access to account ending in {clean_target}")
