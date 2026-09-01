"""Chat pipeline execution workflow integrating PII redaction, routing, and agents."""

from __future__ import annotations

import time

from banking_chat.core.common.types import AgentName, AuthenticatedUser
from banking_chat.modules.accounts.agent import AccountsAgent
from banking_chat.modules.chat.coordinator_agent import CoordinatorAgent
from banking_chat.modules.chat.state import ChatAgentState
from banking_chat.modules.pii_guard.redactor import PIIRedactor
from banking_chat.modules.services.agent import ServiceAgent
from banking_chat.modules.session_memory.conversation import ConversationMemoryManager
from banking_chat.modules.transactions.agent import TransactionsAgent


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
    ) -> None:
        self.coordinator = coordinator or CoordinatorAgent()
        self.accounts_agent = accounts_agent or AccountsAgent()
        self.transactions_agent = transactions_agent or TransactionsAgent()
        self.services_agent = services_agent or ServiceAgent()
        self.redactor = redactor or PIIRedactor()
        self.memory_manager = memory_manager or ConversationMemoryManager()

    async def execute(
        self,
        session_id: str,
        user_message: str,
        user: AuthenticatedUser,
    ) -> ChatAgentState:
        """Run the full chat pipeline sequentially."""
        start_time = time.perf_counter()

        # Step 1: PII Redaction & Tokenization
        redaction = self.redactor.tokenize(user_message)

        # Step 2: Context Retrieval & Routing Intent
        past_history = await self.memory_manager.get_history(session_id)
        target_agent = self.coordinator.route_query(user_message, user, history=past_history)

        # Step 3: Execute target domain agent
        agent_resp: str
        if target_agent == AgentName.ACCOUNTS:
            agent_resp = await self.accounts_agent.run(user_message, user)
        elif target_agent == AgentName.TRANSACTION:
            agent_resp = await self.transactions_agent.run(user_message, user)
        elif target_agent == AgentName.SERVICE:
            agent_resp = await self.services_agent.run(user_message, user)
        else:
            agent_resp = await self.accounts_agent.run(user_message, user)

        # Step 4: Detokenize response if necessary
        final_resp = self.redactor.detokenize(agent_resp, redaction.token_map)

        # Step 5: Persist in conversation memory
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
            cost_usd=0.0001,
            latency_ms=latency_ms,
            error=None,
        )
