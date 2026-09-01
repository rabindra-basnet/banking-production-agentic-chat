"""JWT validation and generation engine supporting Access/Refresh token pairs and token blacklisting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from banking_chat.core.common.exceptions import AuthenticationError, TokenExpiredError
from banking_chat.core.common.token_blacklist import TokenBlacklistManager
from banking_chat.core.common.types import AuthenticatedUser, CustomerTier
from banking_chat.core.config.settings import get_settings
from banking_chat.modules.auth.models import TokenPairDict, TokenPayload


class JWTValidator:
    """Validates and creates JWT Access and Refresh tokens for Bank Identity Provider."""

    def __init__(self, secret_key: str | None = None, algorithm: str | None = None) -> None:
        settings = get_settings()
        self.secret_key = secret_key or settings.app_secret_key
        self.algorithm = algorithm or "HS256"
        self.issuer = settings.auth_idp_issuer
        self.access_expiry_minutes = settings.auth_access_token_expiry_minutes
        self.refresh_expiry_days = settings.auth_refresh_token_expiry_days
        self.blacklist_mgr = TokenBlacklistManager()

    def create_token_pair(
        self,
        customer_id: str = "CIF001234",
        name: str = "Rajesh Kumar",
        email: str = "rajesh.kumar@example.com",
        tier: CustomerTier = CustomerTier.STANDARD,
        accounts: list[str] | None = None,
    ) -> TokenPairDict:
        """Generate a short-lived access token and a long-lived refresh token pair."""
        now = datetime.now(UTC)
        user_id = str(uuid4())
        accounts_list = accounts or ["XXXXXXXXXXXX1234", "XXXXXXXXXXXX5678"]

        # 1. Access Token (Short-lived: default 15 minutes)
        access_exp = now + timedelta(minutes=self.access_expiry_minutes)
        access_payload = {
            "sub": user_id,
            "cif": customer_id,
            "name": name,
            "email": email,
            "tier": str(tier),
            "accounts": accounts_list,
            "roles": ["customer"],
            "token_type": "access",
            "exp": access_exp,
            "iat": now,
            "iss": self.issuer,
            "aud": "banking-chat-app",
        }
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)

        # 2. Refresh Token (Long-lived: default 7 days)
        refresh_exp = now + timedelta(days=self.refresh_expiry_days)
        refresh_payload = {
            "sub": user_id,
            "cif": customer_id,
            "name": name,
            "email": email,
            "tier": str(tier),
            "accounts": accounts_list,
            "token_type": "refresh",
            "exp": refresh_exp,
            "iat": now,
            "iss": self.issuer,
            "aud": "banking-chat-app",
        }
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": self.access_expiry_minutes * 60,
            "cif": customer_id,
        }

    def create_mock_token(
        self,
        customer_id: str = "CIF001234",
        name: str = "Rajesh Kumar",
        email: str = "rajesh.kumar@example.com",
        tier: CustomerTier = CustomerTier.STANDARD,
        accounts: list[str] | None = None,
    ) -> str:
        """Create a mock JWT for local development / testing."""
        now = datetime.now(UTC)
        exp = now + timedelta(minutes=self.access_expiry_minutes)
        payload = {
            "sub": str(uuid4()),
            "cif": customer_id,
            "name": name,
            "email": email,
            "tier": str(tier),
            "accounts": accounts or ["XXXXXXXXXXXX1234", "XXXXXXXXXXXX5678"],
            "roles": ["customer"],
            "token_type": "access",
            "exp": exp,
            "iat": now,
            "iss": self.issuer,
            "aud": "banking-chat-app",
        }
        token: str = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def refresh_access_token(self, refresh_token: str) -> TokenPairDict:
        """Validate a refresh token and issue a new access and rotated refresh token pair."""
        # 1. Check if token is blacklisted
        if self.blacklist_mgr.is_blacklisted_sync(refresh_token):
            raise AuthenticationError("Refresh token has been revoked / blacklisted.")

        return self._rotate_refresh_token(refresh_token)

    async def refresh_access_token_async(self, refresh_token: str) -> TokenPairDict:
        """Validate a refresh token (DB-aware blacklist) and issue a new access token pair."""
        if await self.blacklist_mgr.is_blacklisted(refresh_token):
            raise AuthenticationError("Refresh token has been revoked / blacklisted.")

        return self._rotate_refresh_token(refresh_token)

    def _rotate_refresh_token(self, refresh_token: str) -> TokenPairDict:
        """Shared refresh-token decode and rotation logic."""
        try:
            payload = jwt.decode(
                refresh_token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError as err:
            raise TokenExpiredError() from err
        except JWTError as err:
            raise AuthenticationError(f"Invalid refresh token: {err}") from err

        if payload.get("token_type") != "refresh":
            raise AuthenticationError("Invalid token type provided. Refresh token required.")

        return self.create_token_pair(
            customer_id=payload.get("cif", "CIF001234"),
            name=payload.get("name", "Rajesh Kumar"),
            email=payload.get("email", "rajesh.kumar@example.com"),
            tier=CustomerTier(payload.get("tier", "standard")),
            accounts=payload.get("accounts", []),
        )

    async def validate_token_async(self, token: str) -> AuthenticatedUser:
        """Validate JWT access token against persistent blacklist and return AuthenticatedUser."""
        # 1. Check blacklist (memory + persistent DB across workers)
        if await self.blacklist_mgr.is_blacklisted(token):
            raise AuthenticationError("Access token has been revoked / logged out.")

        return self._decode_access_token(token)

    def validate_token(self, token: str) -> AuthenticatedUser:
        """Validate JWT access token and return AuthenticatedUser (sync, memory blacklist)."""
        # 1. Check blacklist
        if self.blacklist_mgr.is_blacklisted_sync(token):
            raise AuthenticationError("Access token has been revoked / logged out.")

        return self._decode_access_token(token)

    def _decode_access_token(self, token: str) -> AuthenticatedUser:
        """Shared access-token decode and AuthenticatedUser construction."""
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

        expiry_dt = (
            datetime.fromtimestamp(token_payload.exp, tz=UTC)
            if isinstance(token_payload.exp, (int, float))
            else token_payload.exp
        )

        return AuthenticatedUser(
            user_id=user_uuid,
            customer_id=token_payload.cif,
            name=token_payload.name,
            email=token_payload.email,
            tier=token_payload.tier,
            accounts=token_payload.accounts,
            session_id=uuid4(),
            token_expiry=expiry_dt,
        )
