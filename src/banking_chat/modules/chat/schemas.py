"""Pydantic schemas for the Chat Orchestration API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from banking_chat.core.common.types import StrictBaseModel


class ChatMessage(StrictBaseModel):
    """An individual message in a chat thread."""

    role: str = Field(description="Message role (user, assistant, system, tool)")
    content: str = Field(description="Message text content")
    timestamp: datetime | None = Field(default=None, description="Message timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context/metadata")


class ChatRequest(StrictBaseModel):
    """Incoming user chat request payload."""

    message: str = Field(min_length=1, max_length=2000, description="User's query")
    session_id: UUID | None = Field(default=None, description="Optional existing session ID")
    stream: bool = Field(default=False, description="Whether to stream the response via SSE")


class ChatResponse(StrictBaseModel):
    """Outgoing chat response payload."""

    session_id: UUID = Field(description="Chat session ID")
    message: str = Field(description="Assistant's response text")
    routed_agent: str = Field(description="The specialist agent that handled the query")
    cost_usd: float = Field(default=0.0, description="Estimated interaction cost in USD")
    latency_ms: float = Field(default=0.0, description="Processing latency in milliseconds")


class StreamChunk(StrictBaseModel):
    """Chunk delivered during streaming chat responses."""

    session_id: UUID = Field(description="Chat session ID")
    delta: str = Field(description="Incremental text token or chunk")
    is_final: bool = Field(default=False, description="Whether this is the last chunk in stream")


class ConversationHistoryResponse(StrictBaseModel):
    """Historical messages for a given session."""

    session_id: UUID = Field(description="Chat session ID")
    messages: list[ChatMessage] = Field(default_factory=list, description="List of past messages")


class HealthResponse(StrictBaseModel):
    """Service health check response."""

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Timestamp of health check")
