# ADR-002: MCP Server Abstraction for Bank APIs

## Status
Accepted

## Context
Agents calling bank APIs directly creates tight coupling.

## Decision
Use Model Context Protocol (MCP) servers to abstract API integration.

## Consequences
- Agents focus on reasoning, MCP handles API complexity
- API changes don't impact agent logic
- Cleaner separation of concerns
