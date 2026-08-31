# Step-by-Step Architecture Evolution

This document traces the evolution from a simple chatbot to a production-ready system.

See the [architecture diagrams](../../architecturedesigns/) for visual references.

## Step 0: Business Context
A bank receives 4.2 lakh calls/month. 65% are 3 repetitive questions.

## Step 1: Simple Demo
UI → API → Single Agent → LLM

## Step 2: Tool Integration
Agent calls bank's internal APIs (Balance, Transactions, Services)

## Step 3: Multi-Agent
Domain-specific sub-agents reduce tool overload

## Step 4: Coordinator
Central orchestrator plans and routes queries

## Step 5: MCP Servers
Loosely coupled API abstraction layer

## Step 6: Authentication
Bank's identity provider (OIDC/JWT)

## Step 7: Authorization
Role-based access control (Standard/Premium/Privileged)

## Step 8: Session Management
Conversation history + inter-agent shared state

## Step 9: PII Redaction
Sensitive data masking before LLM calls

## Step 10: Hybrid LLM
Self-hosted + third-party routing

## Step 11: Evaluation Suite
Non-deterministic AI testing with golden datasets

## Step 12: Observability
Prompts, agent calls, tool calls monitoring

## Step 13: Cost Tracking
Per-interaction cost monitoring

## Step 14: Edge Security
WAF, rate limits, API gateway
