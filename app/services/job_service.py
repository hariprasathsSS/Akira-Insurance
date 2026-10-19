"""Job service — manages persisted background job status."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import JOB_STATUS_FAILED, JOB_STATUS_QUEUED, ROLE_ADMIN
from app.core.exceptions import Forbidden, ResourceNotFound, ValidationError
from app.db.models.job import BackgroundJob
from app.db.models.user import User
from app.db.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = JobRepository(session)

    async def get_job(self, job_identifier: str, actor: User) -> BackgroundJob:
        if actor.role != ROLE_ADMIN:
            raise Forbidden("Only admins may inspect jobs.")
        job = await self._repo.get_by_public_id(job_identifier)
        if job is None:
            try:
                as_uuid = uuid.UUID(job_identifier)
                job = await self._repo.get_by_id(as_uuid)
            except ValueError:
                pass
        if job is None:
            raise ResourceNotFound(f"Job '{job_identifier}' not found.")
        return job

    async def list_jobs(
        self,
        actor: User,
        status: Optional[str] = None,
        job_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[BackgroundJob]:
        if actor.role != ROLE_ADMIN:
            raise Forbidden("Only admins may list jobs.")
        return await self._repo.get_all(status=status, job_type=job_type, limit=limit, offset=offset)

    async def mark_stuck_jobs_failed(self) -> int:
        """On startup, mark running jobs from prior process as failed."""
        stuck = await self._repo.get_stuck_running_jobs()
        for job in stuck:
            job.status = JOB_STATUS_FAILED
            job.error_code = "WORKER_RESTARTED"
            job.error_message = "Job was running when the worker process restarted. Manual retry required."
            await self._repo.save(job)
        return len(stuck)
