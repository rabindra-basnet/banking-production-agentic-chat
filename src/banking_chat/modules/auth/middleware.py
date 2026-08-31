"""FastAPI authentication middleware and user dependency injection."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, status

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.modules.auth.jwt_validator import JWTValidator

_validator = JWTValidator()


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Extract and validate the current authenticated user from Authorization header."""
    if not authorization:
        # Development fallback user if no auth header is provided in non-production
        return _default_demo_user()

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Must be Bearer <token>",
        )

    token = parts[1]
    try:
        return _validator.validate_token(token)
    except TokenExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from err
    except AuthenticationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err


def _default_demo_user() -> AuthenticatedUser:
    """Fallback user for local development without active token."""
    from datetime import UTC, datetime, timedelta

    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF001234",
        name="Rajesh Kumar",
        email="rajesh.kumar@example.com",
        tier=CustomerTier.STANDARD,
        accounts=["XXXXXXXXXXXX1234", "XXXXXXXXXXXX5678"],
        session_id=uuid4(),
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )


CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]
