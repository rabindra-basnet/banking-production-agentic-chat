# 🏦 Banking Production Agentic Chat — Development Guide

This guide explains how the **Banking Agentic Chat** system routes queries through its **Multi-Agent Pipeline**, executes tools via **Domain MCP Microservices**, and runs the **Streamable React Frontend Simulator**.

---

## 🔒 Multi-Agent Architecture & Tool Routing Flow

The system strictly isolates data access through specialized domain agents and tools:

```
[ User Query (Web / Mobile / React UI) ]
                   │
                   ▼ (FastAPI POST /api/v1/chat)
       [ 1. PII Presidio & Security Guard ]
                   │
                   ▼ (Redacted & Tokenized Context)
       [ 2. Coordinator Intent Router ]
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
 [ Accounts ] [ Transactions ] [ Services ]   (Domain Specialists)
       │           │           │
       ▼           ▼           ▼
 [ Accounts  ] [ Transactions] [ Services ]   (Domain Tools Layer)
 [   Tools   ] [    Tools    ] [  Tools   ]
       │           │           │ (Standard JSON-RPC 2.0 via Streamable MCP)
       ▼           ▼           ▼
 [ MCP Server] [ MCP Server  ] [ MCP Server]  (Ports 9001, 9002, 9003)
 (Port 9001)   (Port 9002)     (Port 9003)
       │           │           │
       └───────────┴───────────┘
                   │
                   ▼
       [ Core Banking & DB Layer ]
```

### Routing Rules:
- **Balance / Account queries** $\rightarrow$ `Coordinator Agent` $\rightarrow$ `Accounts Agent` $\rightarrow$ `Accounts Tools` $\rightarrow$ `Accounts MCP (Port 9001)`
- **Debits / Transfers / Fonepay queries** $\rightarrow$ `Coordinator Agent` $\rightarrow$ `Transactions Agent` $\rightarrow$ `Transactions Tools` $\rightarrow$ `Transactions MCP (Port 9002)`
- **Cheque books / Emergency card blocks** $\rightarrow$ `Coordinator Agent` $\rightarrow$ `Services Agent` $\rightarrow$ `Services Tools` $\rightarrow$ `Services MCP (Port 9003)`
- **Direct external access to internal banking databases is blocked**: Agents only interact through their assigned domain tools.

---

## 📍 Local Development Service Endpoints

| Component | Port / URL | Role |
| :--- | :--- | :--- |
| **React Chat UI Simulator** | [`http://localhost:5173`](http://localhost:5173) | Frontend UI with SSE streaming, profile switcher, and latency badges. |
| **FastAPI Backend Server** | [`http://localhost:8000`](http://localhost:8000) | Core backend with PII filter, Coordinator, and Idempotency engine. |
| **Interactive Swagger Docs** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | Interactive API documentation. |
| **Accounts MCP Microservice**| `http://localhost:9001` | Dedicated microservice for `get_accounts`, `get_account_balance`, `get_account_summary`. |
| **Transactions MCP Microservice**| `http://localhost:9002` | Dedicated microservice for `get_transactions`, `get_spending_summary`. |
| **Services MCP Microservice**| `http://localhost:9003` | Dedicated microservice for `get_service_requests`, `create_service_request`, `block_card`. |

---

## 🚀 Quick Start (All Services with Procfile)

Run all processes simultaneously with **Honcho**:

```bash
honcho start
# OR
make dev
```

---

## 🛠️ Step-by-Step Manual Running

### 1. Install Dependencies
```bash
# Python backend
uv sync --all-extras

# Frontend
cd frontend && npm install && cd ..
```

### 2. Database Migrations & Seeding
```bash
uv run alembic upgrade head
# OR
uv run python scripts/seed_db.py
```

### 3. Run Backend (Terminal 1)
```bash
uv run uvicorn banking_chat.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Run Frontend (Terminal 2)
```bash
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```
Open **`http://localhost:5173`** in your browser.

---

## 🧪 Testing & Verification Commands

```bash
# Run all automated unit and integration tests (44 passed)
uv run pytest

# Build frontend production bundle
cd frontend && npm run build && cd ..

# Code quality check
uv run ruff check src/ tests/
```
