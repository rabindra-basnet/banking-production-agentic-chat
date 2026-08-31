"""Customer services domain service handling service requests and card operations."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from banking_chat.core.common.types import ServiceRequest
from banking_chat.modules.services.models import ServiceRequestModel
from banking_chat.modules.services.schemas import (
    BlockCardRequest,
    BlockCardResponse,
    CreateServiceRequestPayload,
    ServiceRequestListResponse,
)


class CustomerServicesService:
    """Service layer for customer service request workflows."""

    def __init__(self, db_session: AsyncSession | None = None) -> None:
        self.db = db_session

    async def create_service_request(self, customer_id: str, payload: CreateServiceRequestPayload) -> ServiceRequest:
        """Create a new service request."""
        now = datetime.now(UTC)
        req_id = f"SRV-{uuid4().hex[:8].upper()}"
        est_completion = now + timedelta(days=3)

        if self.db is not None:
            model = ServiceRequestModel(
                request_id=req_id,
                customer_id=customer_id,
                type=payload.type,
                status="submitted",
                submitted_at=now,
                estimated_completion=est_completion,
                notes=payload.notes,
            )
            self.db.add(model)
            await self.db.flush()

        return ServiceRequest(
            request_id=req_id,
            type=payload.type,
            status="submitted",
            submitted_at=now,
            estimated_completion=est_completion,
            notes=payload.notes,
        )

    async def get_service_requests(self, customer_id: str) -> ServiceRequestListResponse:
        """Fetch all service requests for a customer."""
        if self.db is not None:
            stmt = (
                select(ServiceRequestModel)
                .where(ServiceRequestModel.customer_id == customer_id)
                .order_by(desc(ServiceRequestModel.submitted_at))
            )
            result = await self.db.execute(stmt)
            records = result.scalars().all()
            requests = [
                ServiceRequest(
                    request_id=m.request_id,
                    type=m.type,  # type: ignore[arg-type]
                    status=m.status,  # type: ignore[arg-type]
                    submitted_at=m.submitted_at,
                    estimated_completion=m.estimated_completion,
                    notes=m.notes,
                )
                for m in records
            ]
        else:
            # Fallback mock data
            now = datetime.now(UTC)
            requests = [
                ServiceRequest(
                    request_id="SRV-CHK89120",
                    type="cheque_book",
                    status="processing",
                    submitted_at=now - timedelta(days=1),
                    estimated_completion=now + timedelta(days=2),
                    notes="25 leaves cheque book",
                )
            ]

        return ServiceRequestListResponse(
            customer_id=customer_id,
            requests=requests,
            total_count=len(requests),
        )

    async def block_card(self, customer_id: str, request: BlockCardRequest) -> BlockCardResponse:
        """Block a customer's debit or credit card immediately."""
        req_id = f"SRV-BLK{uuid4().hex[:6].upper()}"
        if self.db is not None:
            model = ServiceRequestModel(
                request_id=req_id,
                customer_id=customer_id,
                type="card_block",
                status="completed",
                notes=f"Blocked card ending in {request.card_last_four} (reason: {request.reason})",
            )
            self.db.add(model)
            await self.db.flush()

        return BlockCardResponse(
            success=True,
            request_id=req_id,
            card_last_four=request.card_last_four,
            status=f"{request.block_type.capitalize()} Block Active",
            message=f"Card ending in {request.card_last_four} has been successfully {request.block_type} blocked.",
        )
