"""Unit tests for PII redactor and tokenizer."""

from __future__ import annotations

from banking_chat.modules.pii_guard.redactor import PIIRedactor


def test_pii_redactor_tokenize_and_detokenize() -> None:
    redactor = PIIRedactor()
    raw = "Please send OTP to user@bank.com"
    tokenized = redactor.tokenize(raw)

    assert "user@bank.com" not in tokenized.redacted_text
    assert "{{PII_EMAIL_ADDRESS_1}}" in tokenized.redacted_text

    detokenized = redactor.detokenize(tokenized.redacted_text, tokenized.token_map)
    assert detokenized == raw


def test_pii_redactor_mask() -> None:
    redactor = PIIRedactor()
    raw = "My pan is ABCDE1234F"
    masked = redactor.mask(raw)
    assert "<REDACTED>" in masked
    assert "ABCDE1234F" not in masked
