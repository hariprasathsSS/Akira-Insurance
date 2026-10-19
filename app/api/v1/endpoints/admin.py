"""Admin endpoints — document ingestion, version activation/archiving, and job tracking."""
from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.db.models.user import User
from app.rag.ingestion import run_ingestion_job
from app.schemas.document import (
    DocumentActivateRequest,
    DocumentUploadResponse,
    PolicyDocumentListResponse,
    PolicyDocumentResponse,
    PolicyDocumentVersionListResponse,
    PolicyDocumentVersionResponse,
)
from app.schemas.job import BackgroundJobResponse, JobListResponse
from app.services.document_service import DocumentService
from app.services.job_service import JobService

router = APIRouter()


# ── Document Management ───────────────────────────────────────────────────────


@router.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document_version(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    policy_type: str = Form(...),
    plan_tier: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    effective_from: Optional[date] = Form(None),
    effective_to: Optional[date] = Form(None),
    document_public_id: Optional[str] = Form(None),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a new policy document or new version of an existing policy document."""
    file_bytes = await file.read()
    doc_svc = DocumentService(session)

    doc, version, job = await doc_svc.upload_document(
        actor=user,
        file_bytes=file_bytes,
        original_filename=file.filename or "policy.pdf",
        mime_type=file.content_type or "application/pdf",
        policy_type=policy_type,
        plan_tier=plan_tier,
        title=title,
        description=description,
        effective_from=effective_from,
        effective_to=effective_to,
        document_public_id=document_public_id,
    )

    # Schedule background ingestion
    background_tasks.add_task(
        run_ingestion_job,
        job_id=job.id,
        version_id=version.id,
        stored_path=version.stored_path,
        collection_name=version.qdrant_collection,
        metadata={
            "document_public_id": doc.public_id,
            "version_number": version.version_number,
            "policy_type": doc.policy_type,
            "plan_tier": doc.plan_tier,
            "title": doc.title,
        },
    )

    return DocumentUploadResponse(
        document=PolicyDocumentResponse.model_validate(doc),
        version=PolicyDocumentVersionResponse.model_validate(version),
        job_public_id=job.public_id,
    )


@router.get("/documents", response_model=PolicyDocumentListResponse)
async def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentListResponse:
    """List all document families."""
    doc_svc = DocumentService(session)
    docs = await doc_svc.list_documents(actor=user, limit=limit, offset=offset)
    items = [PolicyDocumentResponse.model_validate(d) for d in docs]
    return PolicyDocumentListResponse(items=items, total=len(items))


@router.get(
    "/documents/{document_public_id}/versions",
    response_model=PolicyDocumentVersionListResponse,
)
async def list_document_versions(
    document_public_id: str,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionListResponse:
    """List all immutable versions of a document family."""
    doc_svc = DocumentService(session)
    versions = await doc_svc.list_versions(
        document_public_id=document_public_id, actor=user
    )
    items = [PolicyDocumentVersionResponse.model_validate(v) for v in versions]
    return PolicyDocumentVersionListResponse(items=items, total=len(items))


@router.post(
    "/documents/versions/{version_id}/activate",
    response_model=PolicyDocumentVersionResponse,
)
async def activate_document_version(
    version_id: uuid.UUID,
    req: DocumentActivateRequest = DocumentActivateRequest(),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionResponse:
    """Atomically activate an indexed document version, superseding prior active."""
    doc_svc = DocumentService(session)
    version = await doc_svc.activate_version(version_id=version_id, actor=user)
    return PolicyDocumentVersionResponse.model_validate(version)


@router.post(
    "/documents/versions/{version_id}/archive",
    response_model=PolicyDocumentVersionResponse,
)
async def archive_document_version(
    version_id: uuid.UUID,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionResponse:
    """Archive a document version."""
    doc_svc = DocumentService(session)
    version = await doc_svc.archive_version(version_id=version_id, actor=user)
    return PolicyDocumentVersionResponse.model_validate(version)


# ── Job Tracking ──────────────────────────────────────────────────────────────


@router.get("/jobs", response_model=JobListResponse)
async def list_background_jobs(
    status_filter: Optional[str] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List background ingestion and processing jobs."""
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


@router.get("/jobs/{job_public_id}", response_model=BackgroundJobResponse)
async def get_background_job(
    job_public_id: str,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> BackgroundJobResponse:
    """Inspect status, attempt count, and error state of a background job."""
    job_svc = JobService(session)
    job = await job_svc.get_job(job_public_id=job_public_id, actor=user)
    return BackgroundJobResponse.model_validate(job)
