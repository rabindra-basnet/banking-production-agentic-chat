"""Chat pipeline execution workflow integrating PII redaction, routing, and agents."""

from __future__ import annotations

import json
import logging
import time

from banking_chat.core.common.types import AgentName, AuthenticatedUser
from banking_chat.modules.accounts.agent import AccountsAgent
from banking_chat.modules.chat.coordinator_agent import CoordinatorAgent
from banking_chat.modules.chat.state import ChatAgentState
from banking_chat.modules.llm_gateway.cost_tracker import CostTracker
from banking_chat.modules.pii_guard.redactor import PIIRedactor
from banking_chat.modules.services.agent import ServiceAgent
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager
from banking_chat.modules.transactions.agent import TransactionsAgent

llm_logger = logging.getLogger("banking_chat.modules.llm_gateway")
chat_logger = logging.getLogger("banking_chat.modules.chat")


class ChatPipeline:
    """End-to-end execution pipeline for banking conversational interactions."""

    def __init__(
        self,
        coordinator: CoordinatorAgent | None = None,
        accounts_agent: AccountsAgent | None = None,
        transactions_agent: TransactionsAgent | None = None,
        services_agent: ServiceAgent | None = None,
        redactor: PIIRedactor | None = None,
        memory_manager: ConversationMemoryManager | None = None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self.coordinator = coordinator or CoordinatorAgent()
        self.accounts_agent = accounts_agent or AccountsAgent()
        self.transactions_agent = transactions_agent or TransactionsAgent()
        self.services_agent = services_agent or ServiceAgent()
        self.redactor = redactor or PIIRedactor()
        self.memory_manager = memory_manager or ConversationMemoryManager()
        self.cost_tracker = cost_tracker or CostTracker()

    async def execute(
        self,
        session_id: str,
        user_message: str,
        user: AuthenticatedUser,
    ) -> ChatAgentState:
        """Run the full chat pipeline sequentially."""
        start_time = time.perf_counter()

        # ── Step 1: PII Redaction & Tokenization ──
        llm_logger.info(
            "[PII_GUARD] session=%s customer=%s | Input: %s",
            session_id, user.customer_id, user_message,
        )
        redaction = self.redactor.tokenize(user_message)
        llm_logger.info(
            "[PII_GUARD] session=%s | Redacted: %s | Token map: %s",
            session_id, redaction.redacted_text, json.dumps(redaction.token_map),
        )

        # ── Step 2: Context Retrieval & Routing Intent ──
        past_history = await self.memory_manager.get_history(session_id)
        llm_logger.info(
            "[ROUTER] session=%s | Loaded %d history messages for context",
            session_id, len(past_history),
        )

        target_agent = self.coordinator.route_query(user_message, user, history=past_history)
        llm_logger.info(
            "[ROUTER] session=%s customer=%s | Routed to: %s | Query: %s",
            session_id, user.customer_id, target_agent.value, user_message,
        )

        # ── Step 3: Execute target domain agent ──
        agent_input = redaction.redacted_text if redaction.redacted_text != user_message else user_message
        llm_logger.info(
            "[AGENT_INPUT] session=%s agent=%s | Content: %s",
            session_id, target_agent.value, agent_input,
        )

        agent_resp: str
        tool_calls: list[str] = []
        if target_agent == AgentName.ACCOUNTS:
            agent_resp = await self.accounts_agent.run(agent_input, user, history=past_history)
            tool_calls = self._detect_account_tools(user_message)
        elif target_agent == AgentName.TRANSACTION:
            agent_resp = await self.transactions_agent.run(agent_input, user, history=past_history)
            tool_calls = self._detect_transaction_tools(user_message)
        elif target_agent == AgentName.SERVICE:
            agent_resp = await self.services_agent.run(agent_input, user, history=past_history)
            tool_calls = self._detect_service_tools(user_message)
        else:
            agent_resp = await self.accounts_agent.run(agent_input, user, history=past_history)
            tool_calls = self._detect_account_tools(user_message)

        llm_logger.info(
            "[AGENT_THINKING] session=%s agent=%s | Tool selected: %s | Reasoning: matched domain keywords",
            session_id, target_agent.value, tool_calls if tool_calls else "direct_response",
        )
        llm_logger.info(
            "[AGENT_OUTPUT] session=%s agent=%s | Response: %s",
            session_id, target_agent.value, agent_resp,
        )

        # ── Step 4: Detokenize response if necessary ──
        final_resp = self.redactor.detokenize(agent_resp, redaction.token_map)
        llm_logger.info(
            "[DETOKENIZE] session=%s | Final response: %s",
            session_id, final_resp,
        )

        # ── Step 5: Persist in conversation memory ──
        await self.memory_manager.append_message(
            session_id=session_id,
            customer_id=user.customer_id,
            role="user",
            content=user_message,
        )
        history = await self.memory_manager.append_message(
            session_id=session_id,
            customer_id=user.customer_id,
            role="assistant",
            content=final_resp,
            agent=str(target_agent),
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # ── Step 6: Compute cost from token estimates ──
        prompt_tokens = len(user_message.split()) * 2  # rough token estimate
        completion_tokens = len(final_resp.split()) * 2
        cost_usd = self.cost_tracker.calculate_cost(
            model="llama3.1:8b",
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

        llm_logger.info(
            "[COST] session=%s | model=llama3.1:8b prompt_tokens=%d completion_tokens=%d cost_usd=%.6f latency_ms=%.2f",
            session_id, prompt_tokens, completion_tokens, cost_usd, latency_ms,
        )

        return ChatAgentState(
            session_id=session_id,
            user=user,
            user_message=user_message,
            redacted_message=redaction.redacted_text,
            token_map=redaction.token_map,
            target_agent=str(target_agent),
            agent_response=agent_resp,
            final_response=final_resp,
            history=history,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            error=None,
        )

    @staticmethod
    def _detect_account_tools(query: str) -> list[str]:
        """Detect which account tools were triggered by the query."""
        tools: list[str] = []
        lower = query.lower()
        if any(kw in lower for kw in ["summary", "total", "all account"]):
            tools.append("get_account_summary")
        if any(kw in lower for kw in ["balance", "account", "accounts", "saving", "savings", "fd", "muddati"]):
            tools.append("get_accounts")
        return tools

    @staticmethod
    def _detect_transaction_tools(query: str) -> list[str]:
        """Detect which transaction tools were triggered by the query."""
        tools: list[str] = []
        lower = query.lower()
        if any(kw in lower for kw in ["spending", "summary", "breakdown"]):
            tools.append("get_spending_summary")
        if any(kw in lower for kw in ["transaction", "transactions", "history", "recent"]):
            tools.append("get_transactions")
        return tools

    @staticmethod
    def _detect_service_tools(query: str) -> list[str]:
        """Detect which service tools were triggered by the query."""
        tools: list[str] = []
        lower = query.lower()
        if "block" in lower and ("card" in lower or "debit" in lower or "credit" in lower):
            tools.append("block_card")
        if any(kw in lower for kw in ["cheque", "check book", "checkbook"]):
            tools.append("create_service_request")
        if any(kw in lower for kw in ["service", "request", "ticket", "complaint"]):
            tools.append("get_service_requests")
        return tools
