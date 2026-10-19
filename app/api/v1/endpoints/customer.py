"""Customer endpoints — policies, billing, claims, timeline, and AI chat."""
from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.customer_graph import run_customer_graph
from app.agents.state import AgentState
from app.api.deps import get_db, require_customer
from app.db.models.claim import Claim
from app.db.models.user import User
from app.schemas.billing import BillingListResponse, BillingSummaryResponse
from app.schemas.chat import ChatRequest, ChatResponse, CitationResponse, SuggestedAction
from app.schemas.claim import (
    ClaimCreateRequest,
    ClaimEventResponse,
    ClaimListResponse,
    ClaimResponse,
    ClaimSubmitRequest,
)
from app.schemas.policy import PolicyListResponse, PolicyResponse
from app.services.billing_service import BillingService
from app.services.claim_service import ClaimService
from app.services.policy_service import PolicyService

router = APIRouter()


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


# ── Policies ──────────────────────────────────────────────────────────────────


@router.get("/policies", response_model=PolicyListResponse)
async def list_customer_policies(
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> PolicyListResponse:
    """List all policies owned by the authenticated customer."""
    svc = PolicyService(session)
    policies = await svc.list_policies_for_user(user)
    items = [PolicyResponse.model_validate(p) for p in policies]
    return PolicyListResponse(items=items, total=len(items))


@router.get("/policies/{public_id}", response_model=PolicyResponse)
async def get_customer_policy(
    public_id: str,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> PolicyResponse:
    """Get policy details (customer ownership enforced)."""
    svc = PolicyService(session)
    policy = await svc.get_policy(public_id, user)
    return PolicyResponse.model_validate(policy)


# ── Billing ───────────────────────────────────────────────────────────────────


@router.get("/billing", response_model=BillingListResponse)
async def get_customer_billing(
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> BillingListResponse:
    """Get billing records for policies owned by the authenticated customer."""
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


# ── Claims ────────────────────────────────────────────────────────────────────


@router.post("/claims", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
async def create_claim(
    req: ClaimCreateRequest,
    response: Response,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Lodge a new claim (FNOL). Supports idempotency via idempotency_key."""
    svc = ClaimService(session)
    claim = await svc.create_claim(user, req)
    # If returned claim was existing due to idempotency key replay, set 200 OK
    if claim.idempotency_key == req.idempotency_key and claim.created_at < claim.updated_at:
        response.status_code = status.HTTP_200_OK
    return _to_claim_response(claim)


@router.get("/claims", response_model=ClaimListResponse)
async def list_customer_claims(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimListResponse:
    """List claims created by the authenticated customer."""
    svc = ClaimService(session)
    claims = await svc.list_claims(user, status=status_filter, limit=limit, offset=offset)
    items = [_to_claim_response(c) for c in claims]
    return ClaimListResponse(items=items, total=len(items))


@router.get("/claims/{public_id}", response_model=ClaimResponse)
async def get_customer_claim(
    public_id: str,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Get single claim details (ownership enforced)."""
    svc = ClaimService(session)
    claim = await svc.get_claim(public_id, user)
    return _to_claim_response(claim)


@router.post("/claims/{public_id}/submit", response_model=ClaimResponse)
async def submit_draft_claim(
    public_id: str,
    req: ClaimSubmitRequest = ClaimSubmitRequest(),
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Submit a draft claim for adjuster review."""
    svc = ClaimService(session)
    claim = await svc.submit_claim(public_id, user)
    return _to_claim_response(claim)


@router.get("/claims/{public_id}/timeline", response_model=List[ClaimEventResponse])
async def get_claim_timeline(
    public_id: str,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> List[ClaimEventResponse]:
    """Get historical state transitions and audit events for a claim."""
    svc = ClaimService(session)
    events = await svc.get_events(public_id, user)
    return [ClaimEventResponse.model_validate(e) for e in events]


# ── AI Chat ───────────────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
async def customer_chat(
    req: ChatRequest,
    user: User = Depends(require_customer),
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Chat with the AI assistant for policy inquiries, billing, claims, and RAG."""
    conv_id = req.conversation_id or uuid.uuid4()
    req_id = str(uuid.uuid4())

    state: AgentState = {
        "conversation_id": str(conv_id),
        "request_id": req_id,
        "actor_id": str(user.id),
        "actor_public_id": user.public_id,
        "message": req.message,
        "claim_public_id": req.context.claim_public_id,
        "policy_public_id": req.context.policy_public_id,
        "intent": None,
        "tool_results": {},
        "retrieved_evidence": [],
        "citations": [],
        "response": "",
        "needs_clarification": False,
        "actions": [],
    }

    result_state = await run_customer_graph(state, session=session)

    citations = [
        CitationResponse(
            chunk_id=c.get("chunk_id", ""),
            document_title=c.get("document_title", "Policy Document"),
            section=c.get("section"),
            page=c.get("page"),
            excerpt=c.get("excerpt", ""),
            score=c.get("score", 0.0),
        )
        for c in result_state.get("citations", [])
    ]

    actions = [
        SuggestedAction(
            action_type=a.get("action_type", ""),
            label=a.get("label", ""),
            params=a.get("params", {}),
        )
        for a in result_state.get("actions", [])
    ]

    return ChatResponse(
        conversation_id=conv_id,
        intent=result_state.get("intent") or "UNKNOWN",
        answer=result_state.get("response", ""),
        data=result_state.get("tool_results"),
        citations=citations,
        actions=actions,
        trace_id=req_id,
        needs_clarification=result_state.get("needs_clarification", False),
    )
