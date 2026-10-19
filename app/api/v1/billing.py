"""Billing endpoints per Section 7.3."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_customer
from app.db.models.user import User
from app.schemas.billing import BillingListResponse, BillingSummaryResponse
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/me", response_model=BillingListResponse)
async def get_my_billing(
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> BillingListResponse:
    """Customer: get billing summaries for policies owned by the current user."""
    svc = BillingService(session)
    records = await svc.get_billing_for_user(user)
    items = [
        BillingSummaryResponse(
            policy_public_id=r.policy.public_id if r.policy else "",
            status=r.status,
            amount_due=r.amount_due,
            currency=r.currency,
            due_date=r.due_date,
            last_paid_at=r.last_paid_at,
        )
        for r in records
    ]
    return BillingListResponse(items=items)
