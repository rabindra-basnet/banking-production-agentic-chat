"""Pydantic schemas for the Chat Orchestration API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatMessage(BaseModel):
    """An individual message in a chat thread."""

    model_config = ConfigDict(strict=True)

    role: str = Field(description="Message role (user, assistant, system, tool)")
    content: str = Field(description="Message text content")
    timestamp: datetime | None = Field(default=None, description="Message timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional context/metadata")


class ChatRequest(BaseModel):
    """Incoming user chat request payload."""

    model_config = ConfigDict(strict=True)

    message: str = Field(min_length=1, max_length=2000, description="User's query")
    session_id: UUID | None = Field(default=None, description="Optional existing session ID")
    stream: bool = Field(default=False, description="Whether to stream the response via SSE")


class ChatResponse(BaseModel):
    """Outgoing chat response payload."""

    model_config = ConfigDict(strict=True)

    session_id: UUID = Field(description="Chat session ID")
    message: str = Field(description="Assistant's response text")
    routed_agent: str = Field(description="The specialist agent that handled the query")
    cost_usd: float = Field(default=0.0, description="Estimated interaction cost in USD")
    latency_ms: float = Field(default=0.0, description="Processing latency in milliseconds")


class StreamChunk(BaseModel):
    """Chunk delivered during streaming chat responses."""

    model_config = ConfigDict(strict=True)

    session_id: UUID = Field(description="Chat session ID")
    delta: str = Field(description="Incremental text token or chunk")
    is_final: bool = Field(default=False, description="Whether this is the last chunk in stream")


class ConversationHistoryResponse(BaseModel):
    """Historical messages for a given session."""

    model_config = ConfigDict(strict=True)

    session_id: UUID = Field(description="Chat session ID")
    messages: list[ChatMessage] = Field(default_factory=list, description="List of past messages")


class HealthResponse(BaseModel):
    """Service health check response."""

    model_config = ConfigDict(strict=True)

    status: str = Field(default="healthy", description="Service status")
    version: str = Field(description="Application version")
    timestamp: datetime = Field(description="Timestamp of health check")
