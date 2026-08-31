"""PII detection engine combining pattern matchers and Presidio Analyzer."""

from __future__ import annotations

from typing import Any

from banking_chat.modules.pii_guard.models import PIIDetectionResult, PIIEntity, PIIType
from banking_chat.modules.pii_guard.patterns import (
    AADHAAR_PATTERN,
    ACCOUNT_NUMBER_PATTERN,
    CARD_PATTERN,
    EMAIL_PATTERN,
    IFSC_PATTERN,
    PAN_PATTERN,
    PHONE_PATTERN,
    UPI_ID_PATTERN,
)


class PIIDetector:
    """Detects sensitive PII elements in banking conversations."""

    PATTERNS: list[tuple[PIIType, Any, float]] = [
        (PIIType.PAN, PAN_PATTERN, 0.95),
        (PIIType.AADHAAR, AADHAAR_PATTERN, 0.90),
        (PIIType.IFSC, IFSC_PATTERN, 0.90),
        (PIIType.UPI_ID, UPI_ID_PATTERN, 0.85),
        (PIIType.PHONE, PHONE_PATTERN, 0.85),
        (PIIType.EMAIL, EMAIL_PATTERN, 0.95),
        (PIIType.CREDIT_CARD, CARD_PATTERN, 0.90),
        (PIIType.BANK_ACCOUNT, ACCOUNT_NUMBER_PATTERN, 0.70),
    ]

    def detect(self, text: str) -> PIIDetectionResult:
        """Scan input text and return structured PII detection results."""
        if not text or not text.strip():
            return PIIDetectionResult(has_pii=False, entities=[], entity_counts={})

        entities: list[PIIEntity] = []
        # Keep track of covered spans to avoid overlapping detections
        covered_spans: list[tuple[int, int]] = []

        for pii_type, regex, score in self.PATTERNS:
            for match in regex.finditer(text):
                start, end = match.span()
                # Check overlap
                if any(c_start <= start and end <= c_end for c_start, c_end in covered_spans):
                    continue

                entity = PIIEntity(
                    entity_type=pii_type.value,
                    start=start,
                    end=end,
                    score=score,
                    text=match.group(0),
                )
                entities.append(entity)
                covered_spans.append((start, end))

        # Sort entities by start offset
        entities.sort(key=lambda e: e.start)

        counts: dict[str, int] = {}
        for e in entities:
            counts[e.entity_type] = counts.get(e.entity_type, 0) + 1

        return PIIDetectionResult(
            has_pii=len(entities) > 0,
            entities=entities,
            entity_counts=counts,
        )
