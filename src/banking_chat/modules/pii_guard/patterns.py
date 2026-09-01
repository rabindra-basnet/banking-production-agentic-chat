"""Regex patterns for Nepali, South Asian, and digital banking PII identification."""

from __future__ import annotations

import re

# Nepal National Identity (NID / Rastriya Parichayapatra) & Citizenship No (e.g. 27-01-75-12345 or 123-456-7890)
NEPAL_NID_PATTERN = re.compile(r"\b\d{2}-\d{2}-\d{2}-\d{4,6}\b|\b\d{3}-\d{3}-\d{4}\b")

# PAN (5 letters + 4 digits + 1 letter, or 9 digits)
PAN_PATTERN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b|\b\d{9}\b")

# Aadhaar / 12-digit UID
AADHAAR_PATTERN = re.compile(r"\b[2-9]\d{3}[-\s]?\d{4}[-\s]?\d{4}\b")

# Bank Account Number: 12 to 18 consecutive digits
ACCOUNT_NUMBER_PATTERN = re.compile(r"\b\d{12,18}\b")

# Swift / Branch / Routing / IFSC Code
IFSC_PATTERN = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b|\b[A-Z]{6}[A-Z0-9]{2,5}\b")

# Digital Payment Handles & VPAs (eSewa, Khalti, Fonepay, ConnectIPS, UPI)
UPI_ID_PATTERN = re.compile(r"\b[a-zA-Z0-9.\-_]{2,256}@(esewa|khalti|fonepay|connectips|bank|[a-zA-Z]{2,64})\b")
DIGITAL_WALLET_PATTERN = UPI_ID_PATTERN

# Phone Number (Nepal +977 98/97/96, India +91, 10 digits starting with 6-9)
PHONE_PATTERN = re.compile(r"(?:\+977[-\s]?|\+91[-\s]?)?[6-9]\d{9}\b")

# Email Address
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")

# Credit / Debit Card (13-19 digits, optional spaces/dashes)
CARD_PATTERN = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{1,4}\b")
