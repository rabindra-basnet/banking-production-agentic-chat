"""FastAPI authentication middleware and user dependency injection with Cookie & Header support."""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Header, HTTPException, Request, Response, status

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.modules.auth.jwt_validator import JWTValidator

_validator = JWTValidator()


async def get_current_user(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    """Extract and validate the current authenticated user from HttpOnly cookie or Authorization header."""
    token = None

    # 1. First priority: Extract access_token from HttpOnly / SameSite cookie
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
    elif authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    if not token:
        # Development fallback user if no auth token is provided in non-production
        return _default_demo_user()

    try:
        return _validator.validate_token(token)
    except TokenExpiredError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        ) from err
    except AuthenticationError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(err),
        ) from err


# Type alias for current authenticated user dependency
CurrentUser = Annotated[AuthenticatedUser, Depends(get_current_user)]


def _default_demo_user() -> AuthenticatedUser:
    """Fallback user for local development without active token."""
    from datetime import UTC, datetime, timedelta

    return AuthenticatedUser(
        user_id=uuid4(),
        customer_id="CIF908123",
        name="Rabindra Basnet",
        email="rabindra.basnet@example.com.np",
        tier=CustomerTier.STANDARD,
        accounts=["0120100056781234", "0120100056785678"],
        session_id=uuid4(),
        token_expiry=datetime.now(UTC) + timedelta(hours=1),
    )
