# Main API Application Server (FastAPI with SSE streaming & Idempotency)
backend: uv run uvicorn banking_chat.main:app --reload --host 0.0.0.0 --port 8000

# React Frontend Chat Assistant UI (Vite + TypeScript + Tailwind)
frontend: cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

# Standalone Individual MCP Microservice: Accounts Domain (Port 9001)
mcp-accounts: uv run python src/banking_chat/mcp/accounts/main.py

# Standalone Individual MCP Microservice: Transactions Domain (Port 9002)
mcp-transactions: uv run python src/banking_chat/mcp/transactions/main.py

# Standalone Individual MCP Microservice: Customer Services Domain (Port 9003)
mcp-services: uv run python src/banking_chat/mcp/services/main.py
