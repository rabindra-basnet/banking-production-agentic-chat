"""Unit tests for Database-Backed Persistent Token Blacklisting."""

import pytest
from sqlalchemy import select

from banking_chat.core.common.token_blacklist import RevokedToken, TokenBlacklistManager
from banking_chat.core.db.base import Base
from banking_chat.core.db.session import get_engine, get_session_factory


@pytest.mark.asyncio
async def test_token_persisted_in_database_table() -> None:
    # Ensure database table exists
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    mgr = TokenBlacklistManager()
    dummy_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy_test_token_for_db_blacklist"
    token_hash = mgr.hash_token(dummy_token)

    # 1. Blacklist token
    await mgr.blacklist_token(
        token=dummy_token,
        token_type="refresh",
        customer_id="CIF908123",
        expiry_seconds=3600,
    )

    # 2. Verify token is found in the database table
    factory = get_session_factory()
    async with factory() as session:
        stmt = select(RevokedToken).where(RevokedToken.token_hash == token_hash)
        result = await session.execute(stmt)
        record = result.scalars().first()

        assert record is not None
        assert record.token_hash == token_hash
        assert record.customer_id == "CIF908123"
        assert record.token_type == "refresh"

    # 3. Verify is_blacklisted returns True
    assert await mgr.is_blacklisted(dummy_token) is True
