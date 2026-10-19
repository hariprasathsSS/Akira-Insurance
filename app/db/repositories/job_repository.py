"""Job and Audit repositories."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.job import BackgroundJob
from app.db.models.audit import AuditLog


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_public_id(self, public_id: str) -> Optional[BackgroundJob]:
        result = await self._session.execute(
            select(BackgroundJob).where(BackgroundJob.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, job_id: uuid.UUID) -> Optional[BackgroundJob]:
        result = await self._session.execute(
            select(BackgroundJob).where(BackgroundJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[BackgroundJob]:
        q = select(BackgroundJob)
        if status:
            q = q.where(BackgroundJob.status == status)
        if job_type:
            q = q.where(BackgroundJob.job_type == job_type)
        q = q.order_by(BackgroundJob.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.execute(q)
        return list(result.scalars().all())

    async def get_stuck_running_jobs(self) -> List[BackgroundJob]:
        result = await self._session.execute(
            select(BackgroundJob).where(BackgroundJob.status == "running")
        )
        return list(result.scalars().all())

    async def create(self, job: BackgroundJob) -> BackgroundJob:
        self._session.add(job)
        await self._session.flush()
        return job

    async def save(self, job: BackgroundJob) -> BackgroundJob:
        self._session.add(job)
        await self._session.flush()
        return job


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, log: AuditLog) -> AuditLog:
        self._session.add(log)
        await self._session.flush()
        return log
