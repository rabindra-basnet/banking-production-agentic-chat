"""Unit tests for the Coordinator Agent."""

from __future__ import annotations

from banking_chat.core.common.types import AgentName, AuthenticatedUser
from banking_chat.modules.chat.coordinator_agent import CoordinatorAgent


def test_coordinator_routing_accounts(standard_user: AuthenticatedUser) -> None:
    coordinator = CoordinatorAgent()
    target = coordinator.route_query("What is my current savings account balance?", standard_user)
    assert target == AgentName.ACCOUNTS


def test_coordinator_routing_transactions(standard_user: AuthenticatedUser) -> None:
    coordinator = CoordinatorAgent()
    target = coordinator.route_query("Show me my recent transactions for last week", standard_user)
    assert target == AgentName.TRANSACTION


def test_coordinator_routing_services(standard_user: AuthenticatedUser) -> None:
    coordinator = CoordinatorAgent()
    target = coordinator.route_query("Please block my lost debit card immediately", standard_user)
    assert target == AgentName.SERVICE
