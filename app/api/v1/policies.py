"""Policy endpoints per Section 7.3."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_customer
from app.db.models.user import User
from app.schemas.policy import PolicyListResponse, PolicyResponse
from app.services.policy_service import PolicyService

router = APIRouter(prefix="/policies", tags=["policies"])


@router.get("/me", response_model=PolicyListResponse)
async def list_my_policies(
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> PolicyListResponse:
    """Customer: list only policies owned by the current user."""
    svc = PolicyService(session)
    policies = await svc.list_policies_for_user(user)
    items = [PolicyResponse.model_validate(p) for p in policies]
    return PolicyListResponse(items=items, total=len(items))


@router.get("/{policy_public_id}", response_model=PolicyResponse)
async def get_policy_by_public_id(
    policy_public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> PolicyResponse:
    """Retrieve policy details. Customers may only access their own policies;
    adjusters and admins may view policies within their scope.
    Returns 404 if not found or unauthorized to avoid leaking existence.
    """
    svc = PolicyService(session)
    policy = await svc.get_policy(policy_public_id, user)
    return PolicyResponse.model_validate(policy)
