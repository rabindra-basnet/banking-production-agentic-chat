# ADR-001: Multi-Agent Architecture Pattern

## Status
Accepted

## Context
A single agent with 6+ banking tools leads to tool confusion and reduced accuracy.

## Decision
Adopt a hierarchical multi-agent pattern:
- Coordinator Agent (orchestrator)
- Accounts Agent (balance, statements)
- Transaction Agent (history, disputes)
- Service Agent (requests, card management)

## Consequences
- Better accuracy through domain specialization
- Easier to scale and maintain independently
- Slightly higher latency due to routing overhead
