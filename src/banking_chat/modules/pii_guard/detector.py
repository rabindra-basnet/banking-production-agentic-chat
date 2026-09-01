"""PII detection engine using presidio's NLP analyzer with custom banking patterns."""

from __future__ import annotations

import logging
import os
from typing import Any

from presidio_analyzer import (
    AnalyzerEngine,
    EntityRecognizer,
    Pattern,
    PatternRecognizer,
    RecognizerRegistry,
)
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    EmailRecognizer,
    InPanRecognizer,
    PhoneRecognizer,
)

from banking_chat.core.config.constants import NLP_MODELS_DIR, SPACY_MODEL_LG
from banking_chat.modules.pii_guard.models import PIIDetectionResult, PIIEntity, PIIType
from banking_chat.modules.pii_guard.patterns import (
    AADHAAR_PATTERN,
    ACCOUNT_NUMBER_PATTERN,
    CARD_PATTERN,
    DIGITAL_WALLET_PATTERN,
    EMAIL_PATTERN,
    IFSC_PATTERN,
    NEPAL_NID_PATTERN,
    PAN_PATTERN,
    PHONE_PATTERN,
)

logger = logging.getLogger("banking_chat.modules.pii_guard")

# presidio entity_type -> our PIIType mapping for predefined recognizers
_PRESIDIO_ENTITY_MAP: dict[str, PIIType] = {
    "EMAIL_ADDRESS": PIIType.EMAIL,
    "PHONE_NUMBER": PIIType.PHONE,
    "CREDIT_CARD": PIIType.CREDIT_CARD,
    "IN_AADHAAR": PIIType.AADHAAR,
    "IN_PAN": PIIType.PAN,
}


class PIIDetector:
    """Detects sensitive PII elements in banking conversations.

    Uses presidio's AnalyzerEngine with the large spaCy model (downloaded into
    ``models/``) plus custom pattern recognizers tuned for Nepali and South
    Asian banking identifiers.
    """

    def __init__(self) -> None:
        self._registry = self._build_registry()
        model_name = self._resolve_model()
        nlp_engine = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": model_name}],
            }
        ).create_engine()
        self._engine = AnalyzerEngine(registry=self._registry, nlp_engine=nlp_engine)
        logger.info("PII detector initialised with spaCy model %s", model_name)

    @staticmethod
    def _resolve_model() -> str:
        """Resolve the spaCy model path.

        Prefers the pip-installed package (Docker runtime) by name, otherwise
        locates the model downloaded into models/ (local dev via
        ``scripts/download_models.sh``).
        """
        import spacy

        if spacy.util.is_package(SPACY_MODEL_LG):
            return SPACY_MODEL_LG

        base = os.path.join(NLP_MODELS_DIR, SPACY_MODEL_LG)
        if os.path.isdir(base):
            # spacy download --target nests the loadable package one level down
            for entry in os.listdir(base):
                candidate = os.path.join(base, entry)
                if os.path.isfile(os.path.join(candidate, "config.cfg")):
                    return candidate
            if os.path.isfile(os.path.join(base, "config.cfg")):
                return base
            raise FileNotFoundError(f"'config.cfg' not found under '{base}'.")

        raise FileNotFoundError(
            f"spaCy model '{SPACY_MODEL_LG}' not found. "
            f"Run `./scripts/download_models.sh` (or install it in the image)."
        )

    def _build_registry(self) -> RecognizerRegistry:
        """Build a presidio registry of recognizers.

        Uses presidio's predefined recognizers where they fit, plus custom
        ``PatternRecognizer``s for Nepali/South-Asian banking identifiers
        and patterns whose presidio defaults are too weak (e.g. Aadhaar).
        """
        recognizers: list[EntityRecognizer] = [
            EmailRecognizer(),
            PhoneRecognizer(),
            CreditCardRecognizer(),
            InPanRecognizer(),
        ]

        custom_patterns: list[tuple[str, PIIType, Any, float]] = [
            ("NP_NID_CITIZENSHIP", PIIType.NID, NEPAL_NID_PATTERN, 0.90),
            ("IN_AADHAAR", PIIType.AADHAAR, AADHAAR_PATTERN, 0.90),
            ("IN_PAN", PIIType.PAN, PAN_PATTERN, 0.95),
            ("BRANCH_SWIFT_CODE", PIIType.IFSC, IFSC_PATTERN, 0.90),
            ("DIGITAL_WALLET_VPA", PIIType.UPI_ID, DIGITAL_WALLET_PATTERN, 0.85),
            ("EMAIL_ADDRESS", PIIType.EMAIL, EMAIL_PATTERN, 0.95),
            ("PHONE_NUMBER", PIIType.PHONE, PHONE_PATTERN, 0.85),
            ("CREDIT_CARD", PIIType.CREDIT_CARD, CARD_PATTERN, 0.90),
            ("BANK_ACCOUNT", PIIType.BANK_ACCOUNT, ACCOUNT_NUMBER_PATTERN, 0.70),
        ]
        for name, pii_type, regex, score in custom_patterns:
            pattern = Pattern(name=pii_type.value, regex=regex.pattern, score=score)
            recognizers.append(PatternRecognizer(supported_entity=name, patterns=[pattern]))

        return RecognizerRegistry(recognizers=recognizers)

    def detect(self, text: str) -> PIIDetectionResult:
        """Scan input text and return structured PII detection results."""
        if not text or not text.strip():
            return PIIDetectionResult(has_pii=False, entities=[], entity_counts={})

        raw_results = self._engine.analyze(text=text, language="en")

        entities: list[PIIEntity] = []
        for result in raw_results:
            pii_type = self._map_entity_type(result.entity_type)
            if pii_type is None:
                continue
            entities.append(
                PIIEntity(
                    entity_type=pii_type.value,
                    start=result.start,
                    end=result.end,
                    score=result.score,
                    text=text[result.start : result.end],
                )
            )

        entities = self._resolve_overlaps(entities)
        entities.sort(key=lambda e: e.start)

        entity_counts: dict[str, int] = {}
        for entity in entities:
            entity_counts[entity.entity_type] = entity_counts.get(entity.entity_type, 0) + 1

        return PIIDetectionResult(
            has_pii=len(entities) > 0,
            entities=entities,
            entity_counts=entity_counts,
        )

    @staticmethod
    def _map_entity_type(entity_type: str) -> PIIType | None:
        """Map a presidio entity type to our PIIType enum, or None if unsupported."""
        if entity_type in _PRESIDIO_ENTITY_MAP:
            return _PRESIDIO_ENTITY_MAP[entity_type]
        for pii_type in PIIType:
            if entity_type == pii_type.value:
                return pii_type
        return None

    @staticmethod
    def _resolve_overlaps(entities: list[PIIEntity]) -> list[PIIEntity]:
        """Drop lower-scored entities that overlap a higher-scored one."""
        entities = sorted(entities, key=lambda e: (e.start, -e.score))
        resolved: list[PIIEntity] = []
        for entity in entities:
            if resolved and entity.start < resolved[-1].end:
                previous = resolved[-1]
                if entity.score > previous.score and entity.end > previous.end:
                    resolved[-1] = entity
            else:
                resolved.append(entity)
        return resolved
