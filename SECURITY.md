# Security Policy

## Reporting a Vulnerability
If you discover a security vulnerability, please report it responsibly:
- **Do NOT** open a public GitHub issue
- Email: rabindrabasnet82@gmail.com
- Include: description, reproduction steps, potential impact

## Security Measures
- JWT-based authentication via bank's identity provider
- Role-based access control (RBAC) with tiered permissions
- PII detection and redaction using Microsoft Presidio (MIT license)
- Hybrid LLM routing — sensitive data never leaves the bank's infrastructure
- Rate limiting per customer tier
- Edge layer protection: WAF, DDoS mitigation, API gateway
- All dependencies scanned for CVEs
- Pre-commit hooks block secrets from being committed

## Supported Versions
| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
