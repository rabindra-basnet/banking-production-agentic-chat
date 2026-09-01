"""Data models for PII detection and surrogate tokenization."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PIIType(StrEnum):
    """Supported Personally Identifiable Information types."""

    NID = "NP_NID_CITIZENSHIP"
    AADHAAR = "IN_AADHAAR"
    PAN = "IN_PAN"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    IFSC = "BRANCH_SWIFT_CODE"
    UPI_ID = "DIGITAL_WALLET_VPA"
    PHONE = "PHONE_NUMBER"
    EMAIL = "EMAIL_ADDRESS"
    CREDIT_CARD = "CREDIT_CARD"


class PIIEntity(BaseModel):
    """Detected PII entity within text."""

    model_config = ConfigDict(strict=True)

    entity_type: str = Field(description="Recognized entity type / category")
    start: int = Field(description="Start character index")
    end: int = Field(description="End character index")
    score: float = Field(description="Detection confidence score")
    text: str = Field(description="Extracted raw text snippet")


class PIIDetectionResult(BaseModel):
    """Full result of PII analysis on an input string."""

    model_config = ConfigDict(strict=True)

    has_pii: bool = Field(description="True if any PII was identified")
    entities: list[PIIEntity] = Field(default_factory=list, description="List of recognized entities")
    entity_counts: dict[str, int] = Field(default_factory=dict, description="Count breakdown by type")


class RedactionResult(BaseModel):
    """Outcome of tokenizing or masking sensitive text."""

    model_config = ConfigDict(strict=True)

    redacted_text: str = Field(description="Sanitized text with tokens or masks")
    token_map: dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from surrogate token to raw value",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Redaction operation metadata")
