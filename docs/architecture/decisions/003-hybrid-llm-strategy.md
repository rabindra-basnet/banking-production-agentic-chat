# ADR-003: Hybrid LLM Deployment Strategy

## Status
Accepted

## Context
Sensitive banking data cannot be sent to third-party LLM providers.

## Decision
Deploy hybrid: self-hosted LLM for sensitive data, third-party for complex reasoning.
PII redaction applied before any third-party LLM call.

## Consequences
- Zero PII exposure to external providers
- Self-hosted LLM handles 80%+ of queries (lower cost)
- Complex queries benefit from advanced reasoning capabilities
