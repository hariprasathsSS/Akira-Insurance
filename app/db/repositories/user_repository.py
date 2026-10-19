"""User repository."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_public_id(self, public_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> list[User]:
        result = await self._session.execute(select(User))
        return list(result.scalars().all())

    async def create(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user
