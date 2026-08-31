"""Custom exception hierarchy for the banking chat application."""

from __future__ import annotations


class BankingChatError(Exception):
    """Base exception for all banking chat errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


# ─── Authentication & Authorization ───


class AuthenticationError(BankingChatError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, code="AUTH_FAILED")


class AuthorizationError(BankingChatError):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", required_tier: str = "") -> None:
        self.required_tier = required_tier
        super().__init__(message, code="UNAUTHORIZED")


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired. Please re-authenticate.")


# ─── Agent Errors ───


class AgentError(BankingChatError):
    """Base error for agent-related failures."""

    def __init__(self, message: str, agent_name: str = "") -> None:
        self.agent_name = agent_name
        super().__init__(message, code="AGENT_ERROR")


class AgentRoutingError(AgentError):
    """Raised when the coordinator cannot route to an appropriate agent."""

    def __init__(self, message: str = "Unable to route query to an agent") -> None:
        super().__init__(message)


class ToolExecutionError(AgentError):
    """Raised when an MCP tool call fails."""

    def __init__(self, tool_name: str, message: str = "Tool execution failed") -> None:
        self.tool_name = tool_name
        super().__init__(f"Tool '{tool_name}': {message}")


# ─── Security Errors ───


class PIILeakageError(BankingChatError):
    """Raised when PII is detected in outbound data to third-party LLM."""

    def __init__(self, pii_types: list[str] | None = None) -> None:
        self.pii_types = pii_types or []
        super().__init__("PII detected in outbound data", code="PII_LEAKAGE")


class PromptInjectionError(BankingChatError):
    """Raised when a prompt injection attempt is detected."""

    def __init__(self, message: str = "Potential prompt injection detected") -> None:
        super().__init__(message, code="PROMPT_INJECTION")


class RateLimitExceededError(BankingChatError):
    """Raised when user exceeds rate limits."""

    def __init__(self, retry_after_seconds: int = 300) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__("Rate limit exceeded", code="RATE_LIMITED")


# ─── Cost Errors ───


class CostLimitExceededError(BankingChatError):
    """Raised when interaction cost exceeds the hard limit."""

    def __init__(self, estimated_cost: float, limit: float) -> None:
        self.estimated_cost = estimated_cost
        self.limit = limit
        super().__init__(
            f"Estimated cost ${estimated_cost:.2f} exceeds limit ${limit:.2f}",
            code="COST_LIMIT_EXCEEDED",
        )


# ─── Session Errors ───


class SessionNotFoundError(BankingChatError):
    """Raised when a session cannot be found."""

    def __init__(self, session_id: str = "") -> None:
        super().__init__(f"Session not found: {session_id}", code="SESSION_NOT_FOUND")


class SessionExpiredError(BankingChatError):
    """Raised when a session has expired."""

    def __init__(self) -> None:
        super().__init__("Session has expired. Please start a new conversation.", code="SESSION_EXPIRED")
