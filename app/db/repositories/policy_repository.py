"""Policy repository."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.policy import Policy


class PolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_public_id(self, public_id: str) -> Optional[Policy]:
        result = await self._session.execute(
            select(Policy).where(Policy.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, policy_id: uuid.UUID) -> Optional[Policy]:
        result = await self._session.execute(
            select(Policy).where(Policy.id == policy_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[Policy]:
        result = await self._session.execute(
            select(Policy).where(Policy.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create(self, policy: Policy) -> Policy:
        self._session.add(policy)
        await self._session.flush()
        return policy
