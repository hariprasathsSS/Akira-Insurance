"""Claim endpoints per Section 7.3."""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_customer
from app.db.models.claim import Claim
from app.db.models.user import User
from app.schemas.claim import (
    ClaimCreateRequest,
    ClaimEventResponse,
    ClaimListResponse,
    ClaimResponse,
    ClaimSubmitRequest,
)
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["claims"])


def _to_claim_response(claim: Claim) -> ClaimResponse:
    policy_pub = claim.policy.public_id if claim.policy else ""
    return ClaimResponse(
        public_id=claim.public_id,
        policy_public_id=policy_pub,
        status=claim.status,
        incident_type=claim.incident_type,
        incident_date=claim.incident_date,
        incident_location=claim.incident_location,
        incident_description=claim.incident_description,
        requested_amount=claim.requested_amount,
        recommended_payout=claim.recommended_payout,
        approved_payout=claim.approved_payout,
        fraud_flagged=claim.fraud_flagged,
        submitted_at=claim.submitted_at,
        decided_at=claim.decided_at,
        created_at=claim.created_at,
        updated_at=claim.updated_at,
    )


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    req: ClaimCreateRequest,
    response: Response,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Customer: lodge a new claim (FNOL).
    
    Validates ownership of policy_public_id, validates required fields, and
    enforces idempotency via idempotency_key to prevent duplicate submissions.
    """
    svc = ClaimService(session)
    claim = await svc.create_claim(user, req)
    # If returned claim was pre-existing from an earlier call with the same idempotency key
    if claim.idempotency_key == req.idempotency_key and claim.created_at < claim.updated_at:
        response.status_code = status.HTTP_200_OK
    return _to_claim_response(claim)


@router.get("", response_model=ClaimListResponse)
async def list_claims(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimListResponse:
    """List claims.
    Customers see only their own claims.
    Adjusters and admins see the full claims review queue with optional status filter.
    """
    svc = ClaimService(session)
    claims = await svc.list_claims(user, status=status_filter, limit=limit, offset=offset)
    items = [_to_claim_response(c) for c in claims]
    return ClaimListResponse(items=items, total=len(items))


@router.get("/{claim_public_id}", response_model=ClaimResponse)
async def get_claim(
    claim_public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Retrieve claim details. Enforces ownership for customers (returns 404
    if unauthorized). Adjusters and admins can inspect all claims.
    """
    svc = ClaimService(session)
    claim = await svc.get_claim(claim_public_id, user)
    return _to_claim_response(claim)


@router.post("/{claim_public_id}/submit", response_model=ClaimResponse)
async def submit_draft_claim(
    claim_public_id: str,
    req: ClaimSubmitRequest = ClaimSubmitRequest(),
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Customer: transition draft claim to submitted."""
    svc = ClaimService(session)
    claim = await svc.submit_claim(claim_public_id, user)
    return _to_claim_response(claim)


@router.get("/{claim_public_id}/events", response_model=List[ClaimEventResponse])
async def get_claim_events(
    claim_public_id: str,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> List[ClaimEventResponse]:
    """Retrieve lifecycle events and audit timeline for a claim."""
    svc = ClaimService(session)
    events = await svc.get_events(claim_public_id, user)
    return [ClaimEventResponse.model_validate(e) for e in events]
