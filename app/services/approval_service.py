"""Approval service — human decision and conditional STP.

STP gate: a claim may be auto-approved ONLY if ALL conditions hold:
1. A successful evaluation with calculated recommended_payout exists.
2. recommended_payout < STP_THRESHOLD_INR (configurable, default ₹10,000).
3. No validation flags (fraud or review flags block STP).
4. Policy is active/grace_period.
5. All required claim fields are present.
6. No fraud_flagged == True.
7. The transactional decision write succeeds atomically.

Otherwise, the adjuster must submit an explicit decision via the API.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    CLAIM_STATUS_APPROVED,
    CLAIM_STATUS_DENIED,
    CLAIM_STATUS_PENDING_APPROVAL,
    CLAIM_STATUS_NEEDS_INFORMATION,
    DECISION_APPROVED,
    DECISION_DENIED,
    DECISION_REQUEST_INFORMATION,
    DECISION_AUTO_APPROVED,
    ROLE_ADJUSTER,
)
from app.core.config import get_settings
from app.core.exceptions import (
    ClaimStateConflict,
    EvaluationFailed,
    Forbidden,
    ResourceNotFound,
    ValidationError,
)
from app.db.models.claim import Claim, ClaimDecision
from app.db.models.user import User
from app.db.repositories.claim_repository import ClaimRepository


VALID_DECISIONS = {DECISION_APPROVED, DECISION_DENIED, DECISION_REQUEST_INFORMATION}


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._claim_repo = ClaimRepository(session)
        self._settings = get_settings()

    async def submit_decision(
        self,
        claim_public_id: str,
        actor: User,
        decision: str,
        decision_reason: str,
        approved_amount_str: str,
        evaluation_id: uuid.UUID,
    ) -> ClaimDecision:
        if actor.role != ROLE_ADJUSTER:
            raise Forbidden("Only adjusters may submit claim decisions.")

        if decision not in VALID_DECISIONS:
            raise ValidationError(
                f"Invalid decision '{decision}'. Must be one of: {sorted(VALID_DECISIONS)}."
            )

        claim = await self._claim_repo.get_by_public_id(claim_public_id)
        if claim is None:
            raise ResourceNotFound(f"Claim '{claim_public_id}' not found.")

        # Claim must be in a decidable state
        if claim.status not in (CLAIM_STATUS_PENDING_APPROVAL, "evaluated"):
            raise ClaimStateConflict(
                f"Claim is in status '{claim.status}', which cannot be decided. "
                "Claim must be pending_approval or evaluated."
            )

        # Verify evaluation exists and belongs to this claim
        evaluation = await self._claim_repo.get_evaluation_by_id(evaluation_id)
        if evaluation is None or evaluation.claim_id != claim.id:
            raise ValidationError("Referenced evaluation not found for this claim.")

        # Parse and validate approved amount
        try:
            approved_amount = Decimal(approved_amount_str)
        except Exception:
            raise ValidationError("approved_amount must be a valid decimal number.")

        if approved_amount < Decimal("0"):
            raise ValidationError("approved_amount must be non-negative.")

        if decision == DECISION_APPROVED and not decision_reason.strip():
            raise ValidationError("decision_reason is required for approved decisions.")

        # Determine target claim status
        if decision == DECISION_APPROVED:
            target_status = CLAIM_STATUS_APPROVED
        elif decision == DECISION_DENIED:
            target_status = CLAIM_STATUS_DENIED
        else:  # request_information
            target_status = CLAIM_STATUS_NEEDS_INFORMATION

        # Atomically update claim and create decision
        from app.services.claim_service import ClaimService
        claim_svc = ClaimService(self._session)
        await claim_svc.transition_claim(
            claim, target_status, actor=actor, reason=decision_reason
        )

        if decision == DECISION_APPROVED:
            claim.approved_payout = approved_amount
            claim.decided_at = datetime.now(timezone.utc)
            self._session.add(claim)

        db_decision = ClaimDecision(
            id=uuid.uuid4(),
            claim_id=claim.id,
            evaluation_id=evaluation_id,
            decision=decision,
            decision_reason=decision_reason,
            decided_by_user_id=actor.id,
            approved_amount=approved_amount if decision == DECISION_APPROVED else None,
            is_automated=False,
        )
        await self._claim_repo.create_decision(db_decision)
        return db_decision

    async def attempt_stp(
        self,
        claim: Claim,
        evaluation,
        policy,
    ) -> bool:
        """
        Attempt straight-through processing (auto-approval).
        Returns True if STP succeeded; False if human review is needed.
        All conditions must hold — see module docstring.
        """
        settings = self._settings

        # Condition 1: Evaluation succeeded
        if evaluation.evaluation_status != "succeeded":
            return False

        # Condition 2: Recommended payout below threshold
        if evaluation.recommended_payout is None:
            return False
        if evaluation.recommended_payout >= Decimal(str(settings.STP_THRESHOLD_INR)):
            return False

        # Condition 3: No validation flags
        if evaluation.validation_flags:
            return False

        # Condition 4: Policy status
        if policy.status not in ("active",):
            return False

        # Condition 5: All required fields present
        if not claim.incident_type or not claim.incident_date or not claim.incident_description:
            return False

        # Condition 6: No fraud flag
        if claim.fraud_flagged:
            return False

        # All conditions met — write auto decision atomically
        approved_amount = evaluation.recommended_payout
        claim.approved_payout = approved_amount
        claim.status = CLAIM_STATUS_APPROVED
        claim.decided_at = datetime.now(timezone.utc)
        self._session.add(claim)

        from app.db.models.claim import ClaimEvent
        event = ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim.id,
            from_status=CLAIM_STATUS_PENDING_APPROVAL,
            to_status=CLAIM_STATUS_APPROVED,
            actor_user_id=None,
            reason=f"STP auto-approval: payout {approved_amount} < threshold {settings.STP_THRESHOLD_INR}.",
        )
        self._session.add(event)

        db_decision = ClaimDecision(
            id=uuid.uuid4(),
            claim_id=claim.id,
            evaluation_id=evaluation.id,
            decision=DECISION_AUTO_APPROVED,
            decision_reason=(
                f"Automated STP approval: recommended payout ₹{approved_amount} is below "
                f"configured threshold ₹{settings.STP_THRESHOLD_INR}. "
                "No flags, policy active, all fields present."
            ),
            decided_by_user_id=None,
            approved_amount=approved_amount,
            is_automated=True,
        )
        self._session.add(db_decision)
        return True
