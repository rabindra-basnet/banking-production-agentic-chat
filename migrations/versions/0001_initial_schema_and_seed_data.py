"""Initial schema and seed data for banking production agentic chat.

Revision ID: 0001_initial_schema_and_seed_data
Revises:
Create Date: 2026-09-01 19:23:00.000000

"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial_schema_and_seed_data"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Bank Accounts table
    bank_accounts = op.create_table(
        "bank_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("account_number", sa.String(length=32), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("balance", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("branch_name", sa.String(length=128), nullable=False),
        sa.Column("ifsc_code", sa.String(length=11), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bank_accounts_account_number"), "bank_accounts", ["account_number"], unique=True)
    op.create_index(op.f("ix_bank_accounts_customer_id"), "bank_accounts", ["customer_id"], unique=False)

    # 2. Transactions table
    transactions = op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("transaction_id", sa.String(length=64), nullable=False),
        sa.Column("account_number", sa.String(length=32), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.String(length=256), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("balance_after", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("counterparty", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_transactions_account_number"), "transactions", ["account_number"], unique=False)
    op.create_index(op.f("ix_transactions_customer_id"), "transactions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_transactions_date"), "transactions", ["date"], unique=False)
    op.create_index(op.f("ix_transactions_transaction_id"), "transactions", ["transaction_id"], unique=True)

    # 3. Service Requests table
    service_requests = op.create_table(
        "service_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estimated_completion", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_requests_customer_id"), "service_requests", ["customer_id"], unique=False)
    op.create_index(op.f("ix_service_requests_request_id"), "service_requests", ["request_id"], unique=True)

    # 4. Chat Sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("state_checkpoint", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_sessions_customer_id"), "chat_sessions", ["customer_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_session_id"), "chat_sessions", ["session_id"], unique=True)

    # 5. Insert Dummy Data if seed JSON exists
    seed_file = Path(__file__).resolve().parent.parent.parent / "data" / "seed_banking_data.json"
    if seed_file.exists():
        with open(seed_file, encoding="utf-8") as f:
            customers_data = json.load(f)

        now = datetime.now(UTC)
        for cust in customers_data:
            cust_id = cust["customer_id"]

            for acc in cust.get("accounts", []):
                op.bulk_insert(
                    bank_accounts,
                    [
                        {
                            "id": uuid4(),
                            "customer_id": cust_id,
                            "account_number": acc["account_number"],
                            "account_type": acc["account_type"],
                            "balance": Decimal(str(acc["balance"])),
                            "currency": acc.get("currency", "INR"),
                            "status": acc.get("status", "active"),
                            "branch_name": acc.get("branch_name", "Main Branch"),
                            "ifsc_code": acc.get("ifsc_code", "BANK0000001"),
                            "created_at": now,
                            "updated_at": now,
                        }
                    ],
                )

            for txn in cust.get("transactions", []):
                txn_dt = datetime.fromisoformat(txn["date"].replace("Z", "+00:00"))
                op.bulk_insert(
                    transactions,
                    [
                        {
                            "id": uuid4(),
                            "transaction_id": txn["transaction_id"],
                            "account_number": txn["account_number"],
                            "customer_id": cust_id,
                            "date": txn_dt,
                            "description": txn["description"],
                            "amount": Decimal(str(txn["amount"])),
                            "type": txn["type"],
                            "balance_after": Decimal(str(txn["balance_after"])),
                            "channel": txn.get("channel", "UPI"),
                            "counterparty": txn.get("counterparty"),
                            "created_at": now,
                        }
                    ],
                )

            for srv in cust.get("service_requests", []):
                sub_dt = datetime.fromisoformat(srv["submitted_at"].replace("Z", "+00:00"))
                est_dt = (
                    datetime.fromisoformat(srv["estimated_completion"].replace("Z", "+00:00"))
                    if srv.get("estimated_completion")
                    else None
                )
                op.bulk_insert(
                    service_requests,
                    [
                        {
                            "id": uuid4(),
                            "request_id": srv["request_id"],
                            "customer_id": cust_id,
                            "type": srv["type"],
                            "status": srv.get("status", "submitted"),
                            "submitted_at": sub_dt,
                            "estimated_completion": est_dt,
                            "notes": srv.get("notes"),
                            "created_at": now,
                            "updated_at": now,
                        }
                    ],
                )


def downgrade() -> None:
    op.drop_table("chat_sessions")
    op.drop_table("service_requests")
    op.drop_table("transactions")
    op.drop_table("bank_accounts")
