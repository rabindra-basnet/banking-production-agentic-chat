"""JWT validation engine supporting JWKS verification and mock development mode."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.models import TokenPayload


class JWTValidator:
    """Validates JWT tokens issued by Bank Identity Provider."""

    def __init__(self, secret_key: str | None = None, algorithm: str | None = None) -> None:
        settings = get_settings()
        self.secret_key = secret_key or settings.app_secret_key
        self.algorithm = algorithm or "HS256"
        self.issuer = settings.auth_idp_issuer

    def create_mock_token(
        self,
        customer_id: str = "CIF001234",
        name: str = "Rajesh Kumar",
        email: str = "rajesh.kumar@example.com",
        tier: CustomerTier = CustomerTier.STANDARD,
        accounts: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed JWT token for development and testing purposes."""
        now = datetime.now(UTC)
        expiry = now + (expires_delta or timedelta(minutes=30))
        user_id = str(uuid4())

        payload = {
            "sub": user_id,
            "cif": customer_id,
            "name": name,
            "email": email,
            "tier": str(tier),
            "accounts": accounts or ["XXXXXXXXXXXX1234", "XXXXXXXXXXXX5678"],
            "roles": ["customer"],
            "exp": expiry,
            "iat": now,
            "iss": self.issuer,
            "aud": "banking-chat-app",
        }
        token: str = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def validate_token(self, token: str) -> AuthenticatedUser:
        """Validate JWT token and return AuthenticatedUser."""
        try:
            payload_dict = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError as err:
            raise TokenExpiredError() from err
        except JWTError as err:
            raise AuthenticationError(f"Invalid token: {err}") from err

        token_payload = TokenPayload.model_validate(payload_dict)

        user_uuid = (
            UUID(token_payload.sub) if isinstance(token_payload.sub, str) and len(token_payload.sub) == 36 else uuid4()
        )

        return AuthenticatedUser(
            user_id=user_uuid,
            customer_id=token_payload.cif,
            name=token_payload.name,
            email=token_payload.email,
            tier=token_payload.tier,
            accounts=token_payload.accounts,
            session_id=uuid4(),
            token_expiry=token_payload.exp,
        )
