"""PII masking, surrogate tokenization, and de-tokenization for LLM interactions."""

from __future__ import annotations

from banking_chat.core.config.constants import PII_TOKEN_PREFIX, PII_TOKEN_SUFFIX
from banking_chat.modules.pii_guard.detector import PIIDetector
from banking_chat.modules.pii_guard.models import RedactionResult


class PIIRedactor:
    """Safely replaces PII with reversible surrogate tokens or irreversible masks."""

    def __init__(self, detector: PIIDetector | None = None) -> None:
        self.detector = detector or PIIDetector()

    def tokenize(self, text: str) -> RedactionResult:
        """Replace all detected PII in text with unique surrogate tokens.

        Returns RedactionResult containing tokenized text and mapping back to raw values.
        """
        detection = self.detector.detect(text)
        if not detection.has_pii:
            return RedactionResult(redacted_text=text, token_map={}, metadata={})

        token_map: dict[str, str] = {}
        type_counters: dict[str, int] = {}
        redacted_parts: list[str] = []
        last_idx = 0

        for entity in detection.entities:
            redacted_parts.append(text[last_idx : entity.start])

            type_counters[entity.entity_type] = type_counters.get(entity.entity_type, 0) + 1
            idx = type_counters[entity.entity_type]
            token = f"{PII_TOKEN_PREFIX}{entity.entity_type}_{idx}{PII_TOKEN_SUFFIX}"

            token_map[token] = entity.text
            redacted_parts.append(token)
            last_idx = entity.end

        redacted_parts.append(text[last_idx:])
        redacted_text = "".join(redacted_parts)

        return RedactionResult(
            redacted_text=redacted_text,
            token_map=token_map,
            metadata={"entity_counts": detection.entity_counts},
        )

    def detokenize(self, text: str, token_map: dict[str, str]) -> str:
        """Revert surrogate tokens in text back to original values."""
        result = text
        for token, raw_val in token_map.items():
            result = result.replace(token, raw_val)
        return result

    def mask(self, text: str) -> str:
        """Irreversibly mask all detected PII with generic placeholders (e.g. [REDACTED_EMAIL])."""
        detection = self.detector.detect(text)
        if not detection.has_pii:
            return text

        redacted_parts: list[str] = []
        last_idx = 0

        for entity in detection.entities:
            redacted_parts.append(text[last_idx : entity.start])
            redacted_parts.append(f"[REDACTED_{entity.entity_type}]")
            last_idx = entity.end

        redacted_parts.append(text[last_idx:])
        return "".join(redacted_parts)
