"""Policy service — enforces ownership; never returns other users' data."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import ROLE_ADMIN, ROLE_ADJUSTER, ROLE_CUSTOMER
from app.core.exceptions import Forbidden, ResourceNotFound
from app.db.models.policy import Policy
from app.db.models.user import User
from app.db.repositories.policy_repository import PolicyRepository


class PolicyService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = PolicyRepository(session)

    async def list_policies_for_user(self, user: User) -> List[Policy]:
        """Customer: own policies only."""
        if user.role != ROLE_CUSTOMER:
            raise Forbidden("Only customers may list their own policies via this endpoint.")
        return await self._repo.get_by_user_id(user.id)

    async def get_policy(self, public_id: str, actor: User) -> Policy:
        """Return policy, enforcing ownership for customers."""
        policy = await self._repo.get_by_public_id(public_id)
        if policy is None:
            raise ResourceNotFound(f"Policy '{public_id}' not found.")
        if actor.role == ROLE_CUSTOMER and policy.user_id != actor.id:
            # Return 404 to avoid leaking existence to unauthorized customers
            raise ResourceNotFound(f"Policy '{public_id}' not found.")
        return policy

    async def get_policy_by_id(self, policy_id: uuid.UUID) -> Optional[Policy]:
        return await self._repo.get_by_id(policy_id)
