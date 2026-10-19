"""Admin background job endpoints per Section 7.3."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.models.user import User
from app.schemas.job import BackgroundJobResponse, JobListResponse
from app.services.job_service import JobService

router = APIRouter(prefix="/admin/jobs", tags=["admin-jobs"])


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """Admin: list background jobs with status and type filters."""
    job_svc = JobService(session)
    jobs = await job_svc.list_jobs(
        actor=user,
        status=status_filter,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    items = [BackgroundJobResponse.model_validate(j) for j in jobs]
    return JobListResponse(items=items, total=len(items))


@router.get("/{job_id}", response_model=BackgroundJobResponse)
async def get_job(
    job_id: str,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> BackgroundJobResponse:
    """Admin: get job status, attempts, error message, and result summary."""
    job_svc = JobService(session)
    job = await job_svc.get_job(job_identifier=job_id, actor=user)
    return BackgroundJobResponse.model_validate(job)
