"""Claim service — enforces lifecycle transitions, ownership, and idempotency."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    CLAIM_STATUS_DRAFT,
    CLAIM_STATUS_SUBMITTED,
    CLAIM_STATUS_UNDER_REVIEW,
    CLAIM_TRANSITIONS,
    NOTE_TYPE_CUSTOMER,
    NOTE_TYPE_SYSTEM,
    ROLE_ADJUSTER,
    ROLE_ADMIN,
    ROLE_CUSTOMER,
)
from app.core.exceptions import (
    ClaimStateConflict,
    Forbidden,
    IdempotencyConflict,
    ResourceNotFound,
    ValidationError,
)
from app.db.models.claim import Claim, ClaimEvent, ClaimNote
from app.db.models.policy import Policy
from app.db.models.user import User
from app.db.repositories.claim_repository import ClaimRepository
from app.db.repositories.policy_repository import PolicyRepository
from app.schemas.claim import ClaimCreateRequest


def _assert_valid_transition(current: str, target: str) -> None:
    allowed = CLAIM_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise ClaimStateConflict(
            f"Claim cannot transition from '{current}' to '{target}'. "
            f"Allowed: {sorted(allowed) or 'none'}."
        )


class ClaimService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ClaimRepository(session)
        self._policy_repo = PolicyRepository(session)

    async def create_claim(
        self, actor: User, req: ClaimCreateRequest
    ) -> Claim:
        if actor.role != ROLE_CUSTOMER:
            raise Forbidden("Only customers may create claims.")

        # Idempotency check
        existing = await self._repo.get_by_idempotency_key(actor.id, req.idempotency_key)
        if existing:
            return existing  # Return existing for same key; caller detects 200 vs 201

        # Resolve and own-check policy
        policy = await self._policy_repo.get_by_public_id(req.policy_public_id)
        if policy is None or policy.user_id != actor.id:
            raise ResourceNotFound(f"Policy '{req.policy_public_id}' not found.")

        # Generate deterministic public ID
        count_result = await self._repo.get_all(limit=1, offset=0)
        # Use timestamp-based suffix for uniqueness
        ts = datetime.now(timezone.utc)
        public_id = f"CLM-{ts.strftime('%Y%m%d%H%M%S%f')[:17]}"

        claim = Claim(
            id=uuid.uuid4(),
            public_id=public_id,
            policy_id=policy.id,
            created_by_user_id=actor.id,
            status=CLAIM_STATUS_SUBMITTED,  # Direct submit on creation
            incident_type=req.incident_type,
            incident_date=req.incident_date,
            incident_location=req.incident_location,
            incident_description=req.incident_description,
            requested_amount=req.requested_amount,
            idempotency_key=req.idempotency_key,
            submitted_at=ts,
        )
        await self._repo.create(claim)

        # Record creation event
        event = ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim.id,
            from_status=None,
            to_status=CLAIM_STATUS_SUBMITTED,
            actor_user_id=actor.id,
            reason="Claim submitted via API",
        )
        await self._repo.add_event(event)
        return claim

    async def get_claim(self, public_id: str, actor: User) -> Claim:
        claim = await self._repo.get_by_public_id(public_id)
        if claim is None:
            raise ResourceNotFound(f"Claim '{public_id}' not found.")
        self._enforce_access(claim, actor)
        return claim

    async def list_claims(
        self,
        actor: User,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Claim]:
        if actor.role == ROLE_CUSTOMER:
            return await self._repo.get_by_user_id(actor.id, status=status, limit=limit, offset=offset)
        elif actor.role in (ROLE_ADJUSTER, ROLE_ADMIN):
            return await self._repo.get_all(status=status, limit=limit, offset=offset)
        raise Forbidden("Insufficient role to list claims.")

    async def submit_claim(self, public_id: str, actor: User) -> Claim:
        """Submit a draft claim — only customer/owner can submit."""
        claim = await self._repo.get_by_public_id(public_id)
        if claim is None:
            raise ResourceNotFound(f"Claim '{public_id}' not found.")
        if actor.role != ROLE_CUSTOMER or claim.created_by_user_id != actor.id:
            raise Forbidden("Only the owning customer may submit this claim.")

        _assert_valid_transition(claim.status, CLAIM_STATUS_SUBMITTED)
        old_status = claim.status
        claim.status = CLAIM_STATUS_SUBMITTED
        claim.submitted_at = datetime.now(timezone.utc)
        await self._repo.save(claim)

        event = ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim.id,
            from_status=old_status,
            to_status=CLAIM_STATUS_SUBMITTED,
            actor_user_id=actor.id,
            reason="Customer submitted claim.",
        )
        await self._repo.add_event(event)
        return claim

    async def transition_claim(
        self,
        claim: Claim,
        to_status: str,
        actor: Optional[User] = None,
        reason: Optional[str] = None,
    ) -> Claim:
        _assert_valid_transition(claim.status, to_status)
        old_status = claim.status
        claim.status = to_status
        await self._repo.save(claim)

        event = ClaimEvent(
            id=uuid.uuid4(),
            claim_id=claim.id,
            from_status=old_status,
            to_status=to_status,
            actor_user_id=actor.id if actor else None,
            reason=reason,
        )
        await self._repo.add_event(event)
        return claim

    async def get_events(self, public_id: str, actor: User) -> list:
        claim = await self.get_claim(public_id, actor)
        return await self._repo.get_events(claim.id)

    def _enforce_access(self, claim: Claim, actor: User) -> None:
        if actor.role == ROLE_CUSTOMER and claim.created_by_user_id != actor.id:
            raise ResourceNotFound(f"Claim not found.")
        # Adjuster and admin can view all in this POC
