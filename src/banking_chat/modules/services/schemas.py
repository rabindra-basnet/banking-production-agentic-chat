"""Pydantic schemas for the customer services module."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from banking_chat.core.common.types import ServiceRequest, StrictBaseModel


class CreateServiceRequestPayload(StrictBaseModel):
    """Payload to submit a new service request."""

    type: Literal[
        "cheque_book",
        "address_change",
        "kyc_update",
        "card_block",
        "credit_limit_increase",
        "statement_request",
    ] = Field(description="Type of service request")
    notes: str | None = Field(default=None, description="Optional customer instructions")


class ServiceRequestListResponse(StrictBaseModel):
    """Response payload containing list of customer service requests."""

    customer_id: str = Field(description="Customer CIF")
    requests: list[ServiceRequest] = Field(description="List of active or past service requests")
    total_count: int = Field(description="Total count of requests")


class BlockCardRequest(StrictBaseModel):
    """Payload to immediately block a debit/credit card."""

    card_last_four: str = Field(description="Last 4 digits of the card to block")
    reason: Literal["lost", "stolen", "fraud", "damaged"] = Field(
        default="lost", description="Reason for blocking card"
    )
    block_type: Literal["temporary", "permanent"] = Field(default="permanent", description="Type of block")


class BlockCardResponse(StrictBaseModel):
    """Response payload for card blocking action."""

    success: bool = Field(description="Whether the card was successfully blocked")
    request_id: str = Field(description="Reference ID for this operation")
    card_last_four: str = Field(description="Card last 4 digits")
    status: str = Field(description="New card status")
    message: str = Field(description="Confirmation message")
