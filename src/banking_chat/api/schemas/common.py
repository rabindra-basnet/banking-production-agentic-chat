"""Common response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")
    details: dict | None = Field(default=None, description="Additional error details")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""

    items: list = Field(description="List of items")
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page")
    page_size: int = Field(description="Items per page")
    has_next: bool = Field(description="Whether there are more pages")
