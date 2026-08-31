"""Base agent abstract class defining the interface for all agents."""

from __future__ import annotations

import abc
from typing import Any

from banking_chat.common.types import AuthenticatedUser


class BaseAgent(abc.ABC):
    """Abstract base class for all banking chat agents."""

    def __init__(self, name: str, description: str) -> None:
        self.name = name
        self.description = description

    @abc.abstractmethod
    async def process(
        self,
        message: str,
        user: AuthenticatedUser,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process a user message and return a response.

        Args:
            message: The user's input message.
            user: Authenticated user context.
            context: Optional shared context from other agents.

        Returns:
            Dict with 'response', 'tools_called', and optional metadata.
        """
        ...
