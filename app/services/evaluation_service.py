"""Claim evaluation service — deterministic payout calculation.

POC Assumption: The calculation formula below is illustrative only:
    max(0, min(estimate, applicable_limit) - deductible - approved_adjustments)

This formula does NOT account for depreciation, co-pay, exclusions, sub-limits,
salvage, taxes, or any other line-of-business adjustments not explicitly configured
in this synthetic POC. This MUST be adapted before any real-world use.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    CLAIM_STATUS_EVALUATED,
    CLAIM_STATUS_PENDING_APPROVAL,
    CLAIM_STATUS_APPROVED,
    FLAG_COVERAGE_UNCERTAIN,
    FLAG_FREQUENT_CLAIMS,
    FLAG_POLICY_STATUS_REVIEW,
    NOTE_TYPE_SYSTEM,
    ROLE_ADJUSTER,
)
from app.core.config import get_settings
from app.core.exceptions import EvaluationFailed, Forbidden, ResourceNotFound
from app.db.models.claim import Claim, ClaimEvaluation, ClaimNote
from app.db.models.user import User
from app.db.repositories.claim_repository import ClaimRepository
from app.db.repositories.policy_repository import PolicyRepository
from app.schemas.adjuster import ValidationFlag

INR_ZERO = Decimal("0.00")
TWOPLACES = Decimal("0.01")


def _round(v: Decimal) -> Decimal:
    return v.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def calculate_payout(
    estimate: Decimal,
    deductible: Decimal,
    limit: Decimal,
    approved_adjustments: Decimal = INR_ZERO,
) -> Decimal:
    """
    Deterministic POC payout formula.
    Result = max(0, min(estimate, limit) - deductible - approved_adjustments)
    """
    eligible = min(estimate, limit)
    payout = eligible - deductible - approved_adjustments
    return _round(max(INR_ZERO, payout))


class EvaluationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._claim_repo = ClaimRepository(session)
        self._policy_repo = PolicyRepository(session)
        self._settings = get_settings()

    async def run_evaluation(
        self, claim_public_id: str, actor: User, force_re_eval: bool = False
    ) -> ClaimEvaluation:
        if actor.role != ROLE_ADJUSTER:
            raise Forbidden("Only adjusters may trigger evaluations.")

        claim = await self._claim_repo.get_by_public_id(claim_public_id)
        if claim is None:
            raise ResourceNotFound(f"Claim '{claim_public_id}' not found.")

        policy = await self._policy_repo.get_by_id(claim.policy_id)
        if policy is None:
            raise EvaluationFailed("Policy for claim not found.")

        # ── Extract facts (deterministic in POC; LLM-assisted when available) ──
        extracted_facts = self._extract_facts(claim)

        # ── Validation flags (deterministic) ───────────────────────────────────
        flags = self._run_validation_checks(claim, policy)
        flag_codes = {f.code for f in flags}
        has_blocking_flag = bool(flags)  # Any flag triggers review in POC

        # ── Payout calculation ─────────────────────────────────────────────────
        estimate = claim.requested_amount or INR_ZERO
        deductible = policy.deductible or INR_ZERO
        limit = policy.max_coverage or INR_ZERO

        recommended_payout: Optional[Decimal] = None
        calculation_breakdown: Dict[str, Any] = {}

        if not has_blocking_flag:
            recommended_payout = calculate_payout(estimate, deductible, limit)
            calculation_breakdown = {
                "estimate_amount": str(estimate),
                "deductible_applied": str(deductible),
                "limit_applied": str(limit),
                "approved_adjustments": "0.00",
                "recommended_payout": str(recommended_payout),
                "formula": "max(0, min(estimate, limit) - deductible - adjustments)",
                "note": "POC synthetic calculation only. Not a legally binding figure.",
            }
        else:
            calculation_breakdown = {
                "note": "Calculation deferred — validation flags require human review.",
                "flags": [f.code for f in flags],
            }

        requires_review = has_blocking_flag or (
            recommended_payout is None or recommended_payout >= self._settings.STP_THRESHOLD_INR
        )

        # ── Determine next evaluation version ─────────────────────────────────
        version = await self._claim_repo.next_evaluation_version(claim.id)

        evaluation = ClaimEvaluation(
            id=uuid.uuid4(),
            claim_id=claim.id,
            version=version,
            model_provider=None,
            model_name=None,
            extracted_facts=extracted_facts,
            validation_flags=[f.model_dump() for f in flags],
            coverage_findings={"note": "Coverage review via synthetic policy. Requires human confirmation."},
            estimate_amount=estimate,
            deductible_applied=deductible,
            limit_applied=limit,
            recommended_payout=recommended_payout,
            calculation_breakdown=calculation_breakdown,
            requires_human_review=requires_review,
            evaluation_status="succeeded" if not flags or recommended_payout is not None else "needs_information",
            created_by_user_id=actor.id,
        )
        await self._claim_repo.create_evaluation(evaluation)

        # Update claim status
        new_status = CLAIM_STATUS_EVALUATED if not requires_review else CLAIM_STATUS_PENDING_APPROVAL
        from app.services.claim_service import ClaimService
        svc = ClaimService(self._session)
        await svc.transition_claim(claim, new_status, actor=actor, reason="Evaluation completed.")

        # Update recommended_payout on claim
        if recommended_payout is not None:
            claim.recommended_payout = recommended_payout
            self._claim_repo._session.add(claim)

        return evaluation

    def _extract_facts(self, claim: Claim) -> Dict[str, Any]:
        return {
            "cause_of_loss": claim.incident_type,
            "estimated_damage_amount": str(claim.requested_amount) if claim.requested_amount else None,
            "currency": "INR",
            "incident_date": str(claim.incident_date) if claim.incident_date else None,
            "incident_location": claim.incident_location,
            "incident_description": (claim.incident_description or "")[:500],
            "uncertain_fields": [] if claim.requested_amount else ["estimated_damage_amount"],
            "source": "claim_fields",
            "note": "SYNTHETIC POC — extracted from claim form fields, not LLM inference.",
        }

    def _run_validation_checks(self, claim: Claim, policy) -> List[ValidationFlag]:
        flags = []

        # Policy status check
        if policy.status not in ("active", "grace_period"):
            flags.append(
                ValidationFlag(
                    code=FLAG_POLICY_STATUS_REVIEW,
                    severity="block",
                    description=f"Policy status is '{policy.status}'; claim eligibility uncertain.",
                )
            )

        # Missing required fields
        if not claim.requested_amount or claim.requested_amount <= INR_ZERO:
            flags.append(
                ValidationFlag(
                    code="MISSING_FNOL_FIELDS",
                    severity="block",
                    description="Requested amount is missing or zero.",
                )
            )

        # Amount vs limit
        if claim.requested_amount and policy.max_coverage:
            if claim.requested_amount > policy.max_coverage:
                flags.append(
                    ValidationFlag(
                        code="AMOUNT_EXCEEDS_LIMIT",
                        severity="review",
                        description=f"Requested amount {claim.requested_amount} exceeds coverage limit {policy.max_coverage}.",
                    )
                )

        # Fraud / coverage uncertainty fallback
        if claim.fraud_flagged:
            flags.append(
                ValidationFlag(
                    code=FLAG_COVERAGE_UNCERTAIN,
                    severity="block",
                    description="Claim has been flagged for fraud review.",
                )
            )

        return flags

    async def list_evaluations(self, claim_public_id: str, actor: User) -> List[ClaimEvaluation]:
        if actor.role != ROLE_ADJUSTER:
            raise Forbidden("Only adjusters may list evaluations.")
        claim = await self._claim_repo.get_by_public_id(claim_public_id)
        if claim is None:
            raise ResourceNotFound(f"Claim '{claim_public_id}' not found.")
        return await self._claim_repo.get_evaluations(claim.id)
