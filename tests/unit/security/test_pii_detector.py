"""Unit tests for PII detector."""

from __future__ import annotations

from banking_chat.modules.pii_guard.detector import PIIDetector


def test_pii_detector_pan() -> None:
    detector = PIIDetector()
    res = detector.detect("My PAN number is ABCDE1234F.")
    assert res.has_pii is True
    assert any(e.entity_type == "IN_PAN" for e in res.entities)


def test_pii_detector_email_and_phone() -> None:
    detector = PIIDetector()
    res = detector.detect("Contact me at user@example.com or 9876543210")
    assert res.has_pii is True
    types = [e.entity_type for e in res.entities]
    assert "EMAIL_ADDRESS" in types
    assert "PHONE_NUMBER" in types


def test_pii_detector_clean() -> None:
    detector = PIIDetector()
    res = detector.detect("What are your branch opening hours?")
    assert res.has_pii is False
