"""Document service — admin-only upload, versioning, and activation.

Key invariants (enforced by this service):
- Only admins may upload, activate, archive, or supersede document versions.
- Uploading creates a new immutable version; it never modifies previous rows.
- A new version is NEVER active by default — admin must explicitly activate.
- Activation is atomic: prior active version becomes 'superseded' first.
- A failed ingestion job MUST NOT deactivate the prior active version.
- Archiving is refused if it would leave no active version without a replacement.
"""
from __future__ import annotations

import hashlib
import os
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.constants import (
    DOC_VERSION_INDEXED,
    DOC_VERSION_SUPERSEDED,
    DOC_VERSION_UPLOADED,
    JOB_STATUS_QUEUED,
    JOB_TYPE_POLICY_INGESTION,
    ROLE_ADMIN,
)
from app.core.exceptions import (
    DocumentInvalid,
    DocumentVersionConflict,
    Forbidden,
    ResourceNotFound,
    ValidationError,
)
from app.db.models.document import PolicyDocument, PolicyDocumentVersion
from app.db.models.job import BackgroundJob
from app.db.models.user import User
from app.db.repositories.document_repository import DocumentRepository
from app.db.repositories.job_repository import JobRepository


class DocumentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._doc_repo = DocumentRepository(session)
        self._job_repo = JobRepository(session)
        self._settings = get_settings()

    def _require_admin(self, actor: User) -> None:
        if actor.role != ROLE_ADMIN:
            raise Forbidden("Only admins may manage policy documents.")

    async def upload_document(
        self,
        actor: User,
        file_bytes: bytes,
        original_filename: str,
        mime_type: str,
        policy_type: str,
        plan_tier: str,
        title: str,
        description: Optional[str] = None,
        effective_from: Optional[date] = None,
        effective_to: Optional[date] = None,
        document_public_id: Optional[str] = None,
    ) -> tuple[PolicyDocument, PolicyDocumentVersion, BackgroundJob]:
        self._require_admin(actor)
        settings = self._settings

        # ── File validation ─────────────────────────────────────────────────
        if len(file_bytes) > settings.max_upload_bytes:
            raise DocumentInvalid(
                f"File exceeds maximum size of {settings.MAX_UPLOAD_MB}MB."
            )
        if mime_type not in settings.ALLOWED_UPLOAD_MIME_TYPES:
            raise DocumentInvalid(f"Unsupported MIME type '{mime_type}'.")
        if not original_filename.lower().endswith(".pdf"):
            raise DocumentInvalid("Only PDF files are accepted.")
        # PDF signature check
        if not file_bytes.startswith(b"%PDF"):
            raise DocumentInvalid("File does not appear to be a valid PDF.")

        sha256 = hashlib.sha256(file_bytes).hexdigest()

        # ── Resolve or create document family ───────────────────────────────
        if document_public_id:
            doc = await self._doc_repo.get_document_by_public_id(document_public_id)
            if doc is None:
                raise ResourceNotFound(f"Document family '{document_public_id}' not found.")
        else:
            ts = datetime.now(timezone.utc)
            new_public_id = f"DOC-{policy_type.upper()}-{ts.strftime('%Y%m%d%H%M%S')}"
            doc = PolicyDocument(
                id=uuid.uuid4(),
                public_id=new_public_id,
                policy_type=policy_type,
                plan_tier=plan_tier,
                title=title,
                description=description,
                created_by_user_id=actor.id,
            )
            await self._doc_repo.create_document(doc)

        # ── Determine next version number ────────────────────────────────────
        next_ver = await self._doc_repo.next_version_number(doc.id)

        # ── Save file securely ───────────────────────────────────────────────
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = f"{doc.id}_{next_ver}_{sha256[:8]}.pdf"
        stored_path = os.path.join(upload_dir, safe_name)
        with open(stored_path, "wb") as fh:
            fh.write(file_bytes)

        # ── Create immutable version row ─────────────────────────────────────
        version = PolicyDocumentVersion(
            id=uuid.uuid4(),
            document_id=doc.id,
            version_number=next_ver,
            original_filename=original_filename,
            stored_path=stored_path,
            sha256=sha256,
            mime_type=mime_type,
            file_size_bytes=len(file_bytes),
            effective_from=effective_from,
            effective_to=effective_to,
            status=DOC_VERSION_UPLOADED,
            is_active=False,  # NEVER auto-activate
            qdrant_collection=settings.QDRANT_COLLECTION,
            uploaded_by_user_id=actor.id,
        )
        await self._doc_repo.create_version(version)

        # ── Create background job record ─────────────────────────────────────
        job_public_id = f"JOB-{uuid.uuid4().hex[:12].upper()}"
        job = BackgroundJob(
            id=uuid.uuid4(),
            public_id=job_public_id,
            job_type=JOB_TYPE_POLICY_INGESTION,
            status=JOB_STATUS_QUEUED,
            requested_by_user_id=actor.id,
            resource_id=version.id,
        )
        await self._job_repo.create(job)

        return doc, version, job

    async def activate_version(
        self, version_id: uuid.UUID, actor: User
    ) -> PolicyDocumentVersion:
        self._require_admin(actor)

        version = await self._doc_repo.get_version_by_id(version_id)
        if version is None:
            raise ResourceNotFound(f"Document version '{version_id}' not found.")

        if version.status != DOC_VERSION_INDEXED:
            raise DocumentVersionConflict(
                f"Version must be successfully indexed before activation. "
                f"Current status: '{version.status}'."
            )

        if version.is_active:
            raise DocumentVersionConflict("This version is already active.")

        # Atomically deactivate current active version (supersede, not delete)
        await self._doc_repo.deactivate_all_versions(version.document_id)

        # Activate selected version
        version.is_active = True
        version.status = DOC_VERSION_INDEXED  # remains indexed
        await self._doc_repo.save_version(version)
        return version

    async def archive_version(
        self, version_id: uuid.UUID, actor: User
    ) -> PolicyDocumentVersion:
        self._require_admin(actor)

        version = await self._doc_repo.get_version_by_id(version_id)
        if version is None:
            raise ResourceNotFound(f"Document version '{version_id}' not found.")

        if version.is_active:
            # Check if another indexed version exists
            others = await self._doc_repo.get_versions_for_document(version.document_id)
            other_indexed = [
                v for v in others
                if v.id != version.id and v.status == DOC_VERSION_INDEXED and not v.is_active
            ]
            if not other_indexed:
                raise DocumentVersionConflict(
                    "Cannot archive the only active version without first activating another version."
                )

        version.status = "archived"
        version.is_active = False
        await self._doc_repo.save_version(version)
        return version

    async def list_documents(
        self, actor: User, limit: int = 20, offset: int = 0
    ) -> List[PolicyDocument]:
        self._require_admin(actor)
        return await self._doc_repo.get_all_documents(limit=limit, offset=offset)

    async def list_versions(
        self, document_public_id: str, actor: User
    ) -> List[PolicyDocumentVersion]:
        self._require_admin(actor)
        doc = await self._doc_repo.get_document_by_public_id(document_public_id)
        if doc is None:
            raise ResourceNotFound(f"Document '{document_public_id}' not found.")
        return await self._doc_repo.get_versions_for_document(doc.id)

    async def get_version(
        self, version_id: uuid.UUID, actor: User
    ) -> PolicyDocumentVersion:
        self._require_admin(actor)
        version = await self._doc_repo.get_version_by_id(version_id)
        if version is None:
            raise ResourceNotFound(f"Document version '{version_id}' not found.")
        return version

    async def retry_ingestion(
        self, version_id: uuid.UUID, actor: User
    ) -> tuple[PolicyDocument, PolicyDocumentVersion, BackgroundJob]:
        self._require_admin(actor)
        version = await self._doc_repo.get_version_by_id(version_id)
        if version is None:
            raise ResourceNotFound(f"Document version '{version_id}' not found.")

        if version.status in ("processing", DOC_VERSION_INDEXED):
            raise DocumentVersionConflict(
                f"Cannot retry ingestion for version with status '{version.status}'."
            )

        doc = await self._doc_repo.get_document_by_id(version.document_id)
        if doc is None:
            raise ResourceNotFound("Associated document not found.")

        version.status = DOC_VERSION_UPLOADED
        version.ingestion_error = None
        await self._doc_repo.save_version(version)

        job_public_id = f"JOB-{uuid.uuid4().hex[:12].upper()}"
        job = BackgroundJob(
            id=uuid.uuid4(),
            public_id=job_public_id,
            job_type=JOB_TYPE_POLICY_INGESTION,
            status=JOB_STATUS_QUEUED,
            requested_by_user_id=actor.id,
            resource_id=version.id,
        )
        await self._job_repo.create(job)
        return doc, version, job
