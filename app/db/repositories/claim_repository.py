"""Claim repository."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.claim import Claim, ClaimDecision, ClaimEvaluation, ClaimEvent, ClaimNote


class ClaimRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_public_id(self, public_id: str) -> Optional[Claim]:
        result = await self._session.execute(
            select(Claim)
            .options(joinedload(Claim.policy))
            .where(Claim.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, claim_id: uuid.UUID) -> Optional[Claim]:
        result = await self._session.execute(
            select(Claim)
            .options(joinedload(Claim.policy))
            .where(Claim.id == claim_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Claim]:
        q = select(Claim).options(joinedload(Claim.policy)).where(Claim.created_by_user_id == user_id)
        if status:
            q = q.where(Claim.status == status)
        q = q.order_by(Claim.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_all(
        self,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Claim]:
        q = select(Claim).options(joinedload(Claim.policy))
        if status:
            q = q.where(Claim.status == status)
        q = q.order_by(Claim.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_by_idempotency_key(
        self, user_id: uuid.UUID, key: str
    ) -> Optional[Claim]:
        result = await self._session.execute(
            select(Claim).where(
                Claim.created_by_user_id == user_id,
                Claim.idempotency_key == key,
            )
        )
        return result.scalar_one_or_none()

    async def count_recent_claims_for_policy(
        self, policy_id: uuid.UUID, days: int = 30
    ) -> int:
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self._session.execute(
            select(func.count(Claim.id)).where(
                Claim.policy_id == policy_id,
                Claim.created_at >= cutoff,
            )
        )
        return result.scalar_one()

    async def create(self, claim: Claim) -> Claim:
        self._session.add(claim)
        await self._session.flush()
        return claim

    async def save(self, claim: Claim) -> Claim:
        self._session.add(claim)
        await self._session.flush()
        return claim

    # ── Notes ───────────────────────────────────────────────────────────────

    async def add_note(self, note: ClaimNote) -> ClaimNote:
        self._session.add(note)
        await self._session.flush()
        return note

    async def get_notes(self, claim_id: uuid.UUID) -> List[ClaimNote]:
        result = await self._session.execute(
            select(ClaimNote)
            .where(ClaimNote.claim_id == claim_id)
            .order_by(ClaimNote.created_at)
        )
        return list(result.scalars().all())

    # ── Events ──────────────────────────────────────────────────────────────

    async def add_event(self, event: ClaimEvent) -> ClaimEvent:
        self._session.add(event)
        await self._session.flush()
        return event

    async def get_events(self, claim_id: uuid.UUID) -> List[ClaimEvent]:
        result = await self._session.execute(
            select(ClaimEvent)
            .where(ClaimEvent.claim_id == claim_id)
            .order_by(ClaimEvent.created_at)
        )
        return list(result.scalars().all())

    # ── Evaluations ─────────────────────────────────────────────────────────

    async def next_evaluation_version(self, claim_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.max(ClaimEvaluation.version)).where(
                ClaimEvaluation.claim_id == claim_id
            )
        )
        current_max = result.scalar_one_or_none()
        return (current_max or 0) + 1

    async def create_evaluation(self, evaluation: ClaimEvaluation) -> ClaimEvaluation:
        self._session.add(evaluation)
        await self._session.flush()
        return evaluation

    async def get_evaluations(self, claim_id: uuid.UUID) -> List[ClaimEvaluation]:
        result = await self._session.execute(
            select(ClaimEvaluation)
            .where(ClaimEvaluation.claim_id == claim_id)
            .order_by(ClaimEvaluation.version.desc())
        )
        return list(result.scalars().all())

    async def get_evaluation_by_id(
        self, evaluation_id: uuid.UUID
    ) -> Optional[ClaimEvaluation]:
        result = await self._session.execute(
            select(ClaimEvaluation).where(ClaimEvaluation.id == evaluation_id)
        )
        return result.scalar_one_or_none()

    # ── Decisions ───────────────────────────────────────────────────────────

    async def create_decision(self, decision: ClaimDecision) -> ClaimDecision:
        self._session.add(decision)
        await self._session.flush()
        return decision
