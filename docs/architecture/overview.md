# Architecture Overview

## System Components

The banking agentic chat system consists of the following layers:

### 1. Edge Layer
- WAF (Web Application Firewall)
- DDoS Protection
- Rate Limiting
- API Gateway

### 2. API Layer (FastAPI)
- REST endpoints for chat
- WebSocket/SSE streaming
- Authentication middleware
- Request tracing

### 3. Agent Layer (LangGraph)
- **Coordinator Agent**: Routes queries to specialist agents
- **Accounts Agent**: Balance, account details, statements
- **Transaction Agent**: Transaction history, details, disputes
- **Service Agent**: Cheque books, address changes, KYC, card management

### 4. MCP Layer
- Accounts MCP Server
- Transactions MCP Server
- Services MCP Server

### 5. Security Layer
- Authentication (Bank IdP / OIDC)
- Authorization (RBAC with tiered permissions)
- PII Detection & Redaction (Presidio)

### 6. Data Layer
- Redis (session cache)
- PostgreSQL (checkpoints, audit)

### 7. LLM Layer
- Self-hosted LLM (sensitive data)
- Third-party LLM (complex reasoning)
- Hybrid router

### 8. Observability Layer
- OpenTelemetry tracing
- Prometheus metrics
- AI-specific logging (Langfuse)
- Cost monitoring
