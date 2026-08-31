"""Admin endpoints for cost monitoring and system management."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/admin")


@router.get("/costs")
async def get_cost_dashboard() -> dict[str, Any]:
    """Get LLM cost dashboard data. Admin only."""
    # TODO: Implement (Phase 5)
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.get("/sessions")
async def get_active_sessions() -> dict[str, Any]:
    """Get count of active chat sessions. Admin only."""
    # TODO: Implement (Phase 4)
    raise HTTPException(status_code=501, detail="Not yet implemented")
