"""State representations and TypedDicts for LangGraph workflow execution."""

from __future__ import annotations

from typing import Any, TypedDict

from banking_chat.core.common.types import AuthenticatedUser


class ChatAgentState(TypedDict, total=False):
    """Shared state passed between LangGraph nodes during chat processing."""

    session_id: str
    user: AuthenticatedUser
    user_message: str
    redacted_message: str
    token_map: dict[str, str]
    target_agent: str
    agent_response: str
    final_response: str
    history: list[dict[str, Any]]
    cost_usd: float
    latency_ms: float
    error: str | None
