# 🏦 Banking Production Agentic Chat

Production-grade AI-powered customer support chatbot for banking organizations built with **Vertical Slicing Architecture**, **FastMCP Streamable HTTP Microservices**, and **Enterprise DevSecOps**.

## Architecture

This system uses a **Vertical Slicing Architecture** with domain-specific feature modules and standalone **Streamable HTTP Model Context Protocol (MCP)** microservices.

### Key Features
- 🤖 Multi-agent system (Coordinator → Accounts/Transactions/Services agents)
- 🔌 **Streamable HTTP FastMCP microservices** on ports 9001 (Accounts), 9002 (Transactions), and 9003 (Services)
- 🔐 Layered security: Authentication, RBAC, Presidio PII Masking, Prompt Injection defense
- 🧠 Hybrid LLM routing (self-hosted vLLM/Ollama for sensitive queries, third-party for complex reasoning)
- 💾 Session management with Redis + PostgreSQL checkpointing and Alembic migrations
- 📊 Production structured JSON logging with correlation IDs + OpenTelemetry + Langfuse
- 💸 Per-interaction cost tracking and budget control
- 🧪 AI evaluation suite with golden datasets and strict Mypy / Ruff / Bandit gates
- 📦 Multi-server vertical and horizontal scaling support via Podman Compose and Gunicorn 26 + Uvicorn Workers

---

## Quick Start

### Prerequisites
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- Redis (for sessions)
- PostgreSQL (for checkpoints)
- Podman / Docker (for multi-container deployment)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd banking-production-agentic-chat

# Install all dependencies with uv
make install

# Copy environment variables
cp .env.example .env

# Run Alembic migrations
make migrate

# Run the application in development mode
make run
```

---

## Running with Podman / Docker Compose

You can spin up the entire multi-service ecosystem (FastAPI app, Accounts MCP, Transactions MCP, Services MCP, PostgreSQL, Redis) with a single command:

```bash
# Podman Compose (Recommended for rootless enterprise containers)
make podman-up

# Docker Compose
make docker-up
```

---

## Project Structure & Code References

```text
src/banking_chat/
├── core/                               # Cross-cutting foundational layer
│   ├── config/                         # App settings, constants, and JSON logging
│   ├── db/                             # SQLAlchemy 2.0 Base, engine, async sessions
│   └── common/                         # StrictBaseModel, exceptions, validators, types
│
├── modules/                            # Feature-Driven Vertical Slices
│   ├── chat/                           # LangGraph coordinator agent, API router & graph
│   ├── accounts/                       # Bank accounts domain logic, agent, tools, service
│   ├── transactions/                   # Transactions domain logic, agent, tools, service
│   ├── services/                       # Customer service requests (cards, cheque book, KYC)
│   ├── auth/                           # JWT verification & RBAC authorization policies
│   ├── pii_guard/                      # Microsoft Presidio PII detection & token redactor
│   ├── llm_gateway/                    # Hybrid LLM routing, cost tracker, OpenAI/vLLM clients
│   ├── session_memory/                 # Redis session caching & PostgreSQL checkpointer
│   └── observability/                  # Structured JSON logging, metrics & OpenTelemetry
│
└── mcp/                                # Standalone Deployable Streamable HTTP MCP Hosts
    ├── accounts/                       # Accounts MCP Server (Port 9001)
    ├── transactions/                   # Transactions MCP Server (Port 9002)
    └── services/                       # Services MCP Server (Port 9003)
```

| Subsystem | Source Path | Description |
|---|---|---|
| **Chat API Slice** | [`src/banking_chat/modules/chat/`](src/banking_chat/modules/chat/) | FastAPI coordinator router, LangGraph agent state graph |
| **Accounts Slice** | [`src/banking_chat/modules/accounts/`](src/banking_chat/modules/accounts/) | Account balance inquiry, statement tools, domain models |
| **Transactions Slice** | [`src/banking_chat/modules/transactions/`](src/banking_chat/modules/transactions/) | Transaction history queries, spending analysis tools |
| **Services Slice** | [`src/banking_chat/modules/services/`](src/banking_chat/modules/services/) | Card block, cheque books, KYC service request handlers |
| **MCP Hosts** | [`src/banking_chat/mcp/`](src/banking_chat/mcp/) | Standalone Streamable HTTP FastMCP servers ([Accounts: 9001](src/banking_chat/mcp/accounts/), [Transactions: 9002](src/banking_chat/mcp/transactions/), [Services: 9003](src/banking_chat/mcp/services/)) |
| **Security & PII** | [`src/banking_chat/modules/pii_guard/`](src/banking_chat/modules/pii_guard/) | Microsoft Presidio PII redaction and Indian banking entity patterns |
| **Authentication & RBAC** | [`src/banking_chat/modules/auth/`](src/banking_chat/modules/auth/) | JWT validator with JWKS caching and tier-based RBAC |
| **LLM Gateway** | [`src/banking_chat/modules/llm_gateway/`](src/banking_chat/modules/llm_gateway/) | Hybrid routing with budget controls and token tracking |
| **Session Memory** | [`src/banking_chat/modules/session_memory/`](src/banking_chat/modules/session_memory/) | Redis cache and PostgreSQL async session checkpointer |
| **Observability** | [`src/banking_chat/modules/observability/`](src/banking_chat/modules/observability/) | Prometheus metrics, OpenTelemetry distributed tracing, JSON logs |

---

## Production Deployment & Vertical Scaling

For multi-core vertical scaling in production, Gunicorn 26 is used with Uvicorn worker processes:

```bash
# Run production server using Gunicorn config
make run-prod
```

Worker count is automatically scaled according to available CPU cores or configured via the `WEB_CONCURRENCY` environment variable.

---

## License
MIT License — see [LICENSE](LICENSE) for details.
