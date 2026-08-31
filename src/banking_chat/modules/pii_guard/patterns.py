"""Regex patterns for Indian banking PII identification."""

from __future__ import annotations

import re

# Indian PAN: 5 uppercase letters, 4 digits, 1 uppercase letter
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

# Indian Aadhaar: 12 digits (with optional space/dash separators)
AADHAAR_PATTERN = re.compile(r"\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b")

# Indian Bank Account Number: 9 to 18 consecutive digits
ACCOUNT_NUMBER_PATTERN = re.compile(r"\b\d{9,18}\b")

# Indian IFSC Code: 4 alphabets, digit 0, 6 alphanumeric
IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")

# UPI ID (Virtual Payment Address): user@bank
UPI_ID_PATTERN = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}\b")

# Indian Phone Number (10 digits starting with 6, 7, 8, 9, with optional +91)
PHONE_PATTERN = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}\b")

# Email Address
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

# Credit / Debit Card (13-19 digits, optional spaces/dashes)
CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{1,4}\b")
