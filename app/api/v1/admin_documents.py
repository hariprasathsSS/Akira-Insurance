"""Admin policy document endpoints per Section 7.3."""
from __future__ import annotations

import uuid
from datetime import date
from typing import Optional
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
from app.services.document_service import DocumentService

router = APIRouter(tags=["admin-documents"])


@router.post(
    "/admin/policy-documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_policy_document(
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
    """Admin: upload a new policy document or new version of an existing document.
    
    Returns 202 Accepted and starts background extraction, embedding, and indexing.
    The uploaded version is never activated automatically.
    """
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
        message="Document uploaded. Ingestion job accepted and running in background.",
    )


@router.get(
    "/admin/policy-documents",
    response_model=PolicyDocumentListResponse,
)
async def list_policy_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentListResponse:
    """Admin: paginated list of all document families."""
    doc_svc = DocumentService(session)
    docs = await doc_svc.list_documents(actor=user, limit=limit, offset=offset)
    items = [PolicyDocumentResponse.model_validate(d) for d in docs]
    return PolicyDocumentListResponse(items=items, total=len(items))


@router.get(
    "/admin/policy-documents/{document_public_id}/versions",
    response_model=PolicyDocumentVersionListResponse,
)
async def list_document_versions(
    document_public_id: str,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionListResponse:
    """Admin: list all immutable versions for a document family."""
    doc_svc = DocumentService(session)
    versions = await doc_svc.list_versions(
        document_public_id=document_public_id, actor=user
    )
    items = [PolicyDocumentVersionResponse.model_validate(v) for v in versions]
    return PolicyDocumentVersionListResponse(items=items, total=len(items))


@router.get(
    "/admin/policy-document-versions/{version_id}",
    response_model=PolicyDocumentVersionResponse,
)
async def get_document_version(
    version_id: uuid.UUID,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionResponse:
    """Admin: details, status, indexing result, and error summary for a version."""
    doc_svc = DocumentService(session)
    version = await doc_svc.get_version(version_id=version_id, actor=user)
    return PolicyDocumentVersionResponse.model_validate(version)


@router.post(
    "/admin/policy-document-versions/{version_id}/activate",
    response_model=PolicyDocumentVersionResponse,
)
async def activate_document_version(
    version_id: uuid.UUID,
    req: DocumentActivateRequest = DocumentActivateRequest(),
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionResponse:
    """Admin: atomically activate an indexed version; prior active version becomes superseded."""
    doc_svc = DocumentService(session)
    version = await doc_svc.activate_version(version_id=version_id, actor=user)
    return PolicyDocumentVersionResponse.model_validate(version)


@router.post(
    "/admin/policy-document-versions/{version_id}/retry-ingestion",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_document_ingestion(
    version_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Admin: retry ingestion for a failed document version."""
    doc_svc = DocumentService(session)
    doc, version, job = await doc_svc.retry_ingestion(version_id=version_id, actor=user)

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
        message="Ingestion retry accepted and scheduled in background.",
    )


@router.post(
    "/admin/policy-document-versions/{version_id}/archive",
    response_model=PolicyDocumentVersionResponse,
)
async def archive_document_version(
    version_id: uuid.UUID,
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> PolicyDocumentVersionResponse:
    """Admin: archive a document version. Refuses if it is the only active version."""
    doc_svc = DocumentService(session)
    version = await doc_svc.archive_version(version_id=version_id, actor=user)
    return PolicyDocumentVersionResponse.model_validate(version)
