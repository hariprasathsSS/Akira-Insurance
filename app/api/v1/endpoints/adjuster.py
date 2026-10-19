"""Adjuster endpoints — claim review, notes, evaluations, decisions, transitions."""
from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_adjuster, require_adjuster_or_admin
from app.core.constants import NOTE_TYPE_ADJUSTER
from app.core.exceptions import ResourceNotFound
from app.db.models.claim import Claim, ClaimNote
from app.db.models.user import User
from app.db.repositories.claim_repository import ClaimRepository
from app.schemas.adjuster import (
    AdjusterNoteCreateRequest,
    AdjusterNoteResponse,
    ClaimDecisionRequest,
    ClaimDecisionResponse,
    ClaimEvaluationRequest,
    ClaimEvaluationResponse,
    ClaimTransitionRequest,
    ValidationFlag,
)
from app.schemas.claim import ClaimListResponse, ClaimResponse
from app.services.approval_service import ApprovalService
from app.services.claim_service import ClaimService
from app.services.evaluation_service import EvaluationService

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


# ── Claims queue & inspection ─────────────────────────────────────────────────


@router.get("/claims", response_model=ClaimListResponse)
async def list_claims_for_review(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_adjuster_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ClaimListResponse:
    """List all claims for review with optional status filter."""
    svc = ClaimService(session)
    claims = await svc.list_claims(user, status=status_filter, limit=limit, offset=offset)
    items = [_to_claim_response(c) for c in claims]
    return ClaimListResponse(items=items, total=len(items))


@router.get("/claims/{public_id}", response_model=ClaimResponse)
async def get_claim_detail(
    public_id: str,
    user: User = Depends(require_adjuster_or_admin),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Inspect full details of any claim."""
    svc = ClaimService(session)
    claim = await svc.get_claim(public_id, user)
    return _to_claim_response(claim)


@router.post("/claims/{public_id}/transition", response_model=ClaimResponse)
async def transition_claim_status(
    public_id: str,
    req: ClaimTransitionRequest,
    user: User = Depends(require_adjuster),
    session: AsyncSession = Depends(get_db),
) -> ClaimResponse:
    """Explicitly transition claim state (e.g., under_review, needs_information)."""
    svc = ClaimService(session)
    claim = await svc.get_claim(public_id, user)
    updated = await svc.transition_claim(
        claim=claim,
        to_status=req.to_status,
        actor=user,
        reason=req.reason,
    )
    return _to_claim_response(updated)


# ── Adjuster notes ────────────────────────────────────────────────────────────


@router.post(
    "/claims/{public_id}/notes",
    response_model=AdjusterNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_claim_note(
    public_id: str,
    req: AdjusterNoteCreateRequest,
    user: User = Depends(require_adjuster),
    session: AsyncSession = Depends(get_db),
) -> AdjusterNoteResponse:
    """Add an internal adjuster note to a claim."""
    claim_repo = ClaimRepository(session)
    claim = await claim_repo.get_by_public_id(public_id)
    if claim is None:
        raise ResourceNotFound(f"Claim '{public_id}' not found.")

    note = ClaimNote(
        id=uuid.uuid4(),
        claim_id=claim.id,
        author_user_id=user.id,
        note_type=NOTE_TYPE_ADJUSTER,
        note_text=req.note_text,
    )
    saved_note = await claim_repo.add_note(note)
    claim.adjuster_notes_latest = req.note_text
    await claim_repo.save(claim)

    return AdjusterNoteResponse(
        id=saved_note.id,
        claim_id=saved_note.claim_id,
        note_type=saved_note.note_type,
        note_text=saved_note.note_text,
        created_at=saved_note.created_at,
    )


@router.get("/claims/{public_id}/notes", response_model=List[AdjusterNoteResponse])
async def list_claim_notes(
    public_id: str,
    user: User = Depends(require_adjuster_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[AdjusterNoteResponse]:
    """List all notes recorded for a claim."""
    claim_repo = ClaimRepository(session)
    claim = await claim_repo.get_by_public_id(public_id)
    if claim is None:
        raise ResourceNotFound(f"Claim '{public_id}' not found.")

    notes = await claim_repo.get_notes(claim.id)
    return [
        AdjusterNoteResponse(
            id=n.id,
            claim_id=n.claim_id,
            note_type=n.note_type,
            note_text=n.note_text,
            created_at=n.created_at,
        )
        for n in notes
    ]


# ── Evaluation ────────────────────────────────────────────────────────────────


@router.post("/claims/{public_id}/evaluate", response_model=ClaimEvaluationResponse)
async def evaluate_claim(
    public_id: str,
    req: ClaimEvaluationRequest = ClaimEvaluationRequest(),
    user: User = Depends(require_adjuster),
    session: AsyncSession = Depends(get_db),
) -> ClaimEvaluationResponse:
    """Run deterministic payout calculation, rule validations, and STP checks."""
    eval_svc = EvaluationService(session)
    evaluation = await eval_svc.run_evaluation(
        claim_public_id=public_id,
        actor=user,
        force_re_eval=req.force_re_evaluation,
    )

    flags = [
        ValidationFlag(
            code=f.get("code", ""),
            severity=f.get("severity", "review"),
            description=f.get("description", ""),
        )
        for f in (evaluation.validation_flags or [])
    ]

    return ClaimEvaluationResponse(
        evaluation_id=evaluation.id,
        claim_public_id=public_id,
        version=evaluation.version,
        extracted_facts=evaluation.extracted_facts or {},
        validation_flags=flags,
        coverage_findings=evaluation.coverage_findings or {},
        calculation_breakdown=evaluation.calculation_breakdown or {},
        recommended_payout=str(evaluation.recommended_payout)
        if evaluation.recommended_payout is not None
        else None,
        requires_human_review=evaluation.requires_human_review,
        evaluation_status=evaluation.evaluation_status,
        trace_id=evaluation.trace_id or "",
    )


@router.get("/claims/{public_id}/evaluations", response_model=List[ClaimEvaluationResponse])
async def list_claim_evaluations(
    public_id: str,
    user: User = Depends(require_adjuster_or_admin),
    session: AsyncSession = Depends(get_db),
) -> List[ClaimEvaluationResponse]:
    """List historical evaluation runs for a claim."""
    claim_repo = ClaimRepository(session)
    claim = await claim_repo.get_by_public_id(public_id)
    if claim is None:
        raise ResourceNotFound(f"Claim '{public_id}' not found.")

    evaluations = await claim_repo.get_evaluations(claim.id)
    results = []
    for ev in evaluations:
        flags = [
            ValidationFlag(
                code=f.get("code", ""),
                severity=f.get("severity", "review"),
                description=f.get("description", ""),
            )
            for f in (ev.validation_flags or [])
        ]
        results.append(
            ClaimEvaluationResponse(
                evaluation_id=ev.id,
                claim_public_id=public_id,
                version=ev.version,
                extracted_facts=ev.extracted_facts or {},
                validation_flags=flags,
                coverage_findings=ev.coverage_findings or {},
                calculation_breakdown=ev.calculation_breakdown or {},
                recommended_payout=str(ev.recommended_payout)
                if ev.recommended_payout is not None
                else None,
                requires_human_review=ev.requires_human_review,
                evaluation_status=ev.evaluation_status,
                trace_id=ev.trace_id or "",
            )
        )
    return results


# ── Decision ──────────────────────────────────────────────────────────────────


@router.post("/claims/{public_id}/decide", response_model=ClaimDecisionResponse)
async def decide_claim(
    public_id: str,
    req: ClaimDecisionRequest,
    user: User = Depends(require_adjuster),
    session: AsyncSession = Depends(get_db),
) -> ClaimDecisionResponse:
    """Submit adjuster approval, denial, or request for information."""
    appr_svc = ApprovalService(session)
    decision = await appr_svc.submit_decision(
        claim_public_id=public_id,
        actor=user,
        decision=req.decision,
        decision_reason=req.decision_reason,
        approved_amount_str=req.approved_amount,
        evaluation_id=req.evaluation_id,
    )
    return ClaimDecisionResponse(
        decision_id=decision.id,
        claim_public_id=public_id,
        decision=decision.decision,
        approved_amount=str(decision.approved_amount or "0.00"),
        is_automated=decision.is_automated,
        created_at=decision.created_at,
    )
