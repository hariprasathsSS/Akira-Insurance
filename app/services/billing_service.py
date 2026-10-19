"""Billing service."""
from __future__ import annotations

from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ROLE_CUSTOMER
from app.core.exceptions import Forbidden
from app.db.models.billing import BillingRecord
from app.db.models.user import User
from app.db.repositories.billing_repository import BillingRepository


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = BillingRepository(session)

    async def get_billing_for_user(self, actor: User) -> List[BillingRecord]:
        if actor.role != ROLE_CUSTOMER:
            raise Forbidden("Only customers may access their billing summary.")
        return await self._repo.get_by_user_id(actor.id)
