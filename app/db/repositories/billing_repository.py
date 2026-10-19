"""Billing repository."""
from __future__ import annotations

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.db.models.billing import BillingRecord
from app.db.models.policy import Policy


class BillingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_user_id(self, user_id: uuid.UUID) -> List[BillingRecord]:
        """Return billing records for policies owned by user_id."""
        result = await self._session.execute(
            select(BillingRecord)
            .join(Policy, Policy.id == BillingRecord.policy_id)
            .options(joinedload(BillingRecord.policy))
            .where(Policy.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get_by_policy_id(self, policy_id: uuid.UUID) -> List[BillingRecord]:
        result = await self._session.execute(
            select(BillingRecord).where(BillingRecord.policy_id == policy_id)
        )
        return list(result.scalars().all())

    async def create(self, record: BillingRecord) -> BillingRecord:
        self._session.add(record)
        await self._session.flush()
        return record
