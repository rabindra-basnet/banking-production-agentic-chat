import logging

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig, RecognizerResult

from banking_chat.core.config.constants import PII_TOKEN_PREFIX, PII_TOKEN_SUFFIX
from banking_chat.modules.pii_guard.detector import PIIDetector
from banking_chat.modules.pii_guard.models import PIIEntity, RedactionResult

logger = logging.getLogger("banking_chat.modules.pii_guard")


class PIIRedactor:
    """Safely replaces PII with reversible surrogate tokens or irreversible masks.

    Detection is delegated to presidio's AnalyzerEngine (via PIIDetector);
    anonymization uses presidio's AnonymizerEngine with OperatorConfig.
    """

    def __init__(self, detector: PIIDetector | None = None) -> None:
        self.detector = detector or PIIDetector()
        self._anonymizer = AnonymizerEngine()  # type: ignore[no-untyped-call]

    def _to_recognizer_results(self, entities: list[PIIEntity]) -> list[RecognizerResult]:
        return [
            RecognizerResult(
                entity_type=e.entity_type,
                start=e.start,
                end=e.end,
                score=e.score,
            )
            for e in entities
        ]

    def tokenize(self, text: str) -> RedactionResult:
        """Replace all detected PII in text with unique surrogate tokens.

        Returns RedactionResult containing tokenized text and mapping back to raw values.
        """
        detection = self.detector.detect(text)
        if not detection.has_pii:
            return RedactionResult(redacted_text=text, token_map={}, metadata={})

        logger.info(f"PII detected: entity_types={[e.entity_type for e in detection.entities]}")

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
        """Irreversibly mask all detected PII via presidio's AnonymizerEngine.

        Phone numbers/credit cards are partially masked; everything else is
        replaced with a generic <REDACTED> placeholder.
        """
        detection = self.detector.detect(text)
        if not detection.has_pii:
            return text

        operators = {
            "DEFAULT": OperatorConfig("replace", {"new_value": "<REDACTED>"}),
            "PHONE_NUMBER": OperatorConfig(
                "mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 6, "from_end": True}
            ),
            "CREDIT_CARD": OperatorConfig(
                "mask", {"type": "mask", "masking_char": "*", "chars_to_mask": 4, "from_end": True}
            ),
        }
        result = self._anonymizer.anonymize(
            text=text,
            analyzer_results=self._to_recognizer_results(detection.entities),
            operators=operators,
        )
        return result.text
