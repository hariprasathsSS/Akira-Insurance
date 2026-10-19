"""Unit tests for document versioning and activation invariants per Section 8 and 16."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.constants import (
    DOC_VERSION_INDEXED,
    DOC_VERSION_PROCESSING,
    DOC_VERSION_UPLOADED,
    ROLE_ADMIN,
    ROLE_CUSTOMER,
)
from app.core.exceptions import DocumentVersionConflict, Forbidden
from app.db.models.document import PolicyDocument, PolicyDocumentVersion
from app.db.models.user import User
from app.services.document_service import DocumentService


@pytest.fixture
def admin_user():
    return User(
        id=uuid.uuid4(),
        public_id="U-901",
        name="Admin",
        role=ROLE_ADMIN,
        is_active=True,
    )


@pytest.fixture
def customer_user():
    return User(
        id=uuid.uuid4(),
        public_id="U-101",
        name="Customer",
        role=ROLE_CUSTOMER,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_non_admin_cannot_activate_version(customer_user):
    """Customer role is forbidden from managing documents."""
    session = MagicMock()
    svc = DocumentService(session)
    with pytest.raises(Forbidden):
        await svc.activate_version(uuid.uuid4(), customer_user)


@pytest.mark.asyncio
async def test_activation_fails_if_not_indexed(admin_user):
    """Cannot activate a document version that is still processing or failed."""
    session = MagicMock()
    doc_repo = MagicMock()
    version = PolicyDocumentVersion(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        version_number=1,
        status=DOC_VERSION_PROCESSING,
        is_active=False,
    )
    doc_repo.get_version_by_id = AsyncMock(return_value=version)

    svc = DocumentService(session)
    svc._doc_repo = doc_repo

    with pytest.raises(DocumentVersionConflict) as exc:
        await svc.activate_version(version.id, admin_user)
    assert "must be successfully indexed" in str(exc.value)


@pytest.mark.asyncio
async def test_activation_supersedes_prior_active(admin_user):
    """Activating version 2 must deactivate version 1."""
    session = MagicMock()
    doc_repo = MagicMock()
    doc_id = uuid.uuid4()

    ver2 = PolicyDocumentVersion(
        id=uuid.uuid4(),
        document_id=doc_id,
        version_number=2,
        status=DOC_VERSION_INDEXED,
        is_active=False,
    )
    doc_repo.get_version_by_id = AsyncMock(return_value=ver2)
    doc_repo.deactivate_all_versions = AsyncMock()
    doc_repo.save_version = AsyncMock(return_value=ver2)

    svc = DocumentService(session)
    svc._doc_repo = doc_repo

    activated = await svc.activate_version(ver2.id, admin_user)
    assert activated.is_active is True
    doc_repo.deactivate_all_versions.assert_awaited_once_with(doc_id)


@pytest.mark.asyncio
async def test_cannot_archive_only_active_version(admin_user):
    """Cannot archive the sole active version without a replacement."""
    session = MagicMock()
    doc_repo = MagicMock()
    doc_id = uuid.uuid4()

    ver1 = PolicyDocumentVersion(
        id=uuid.uuid4(),
        document_id=doc_id,
        version_number=1,
        status=DOC_VERSION_INDEXED,
        is_active=True,
    )
    doc_repo.get_version_by_id = AsyncMock(return_value=ver1)
    # No other versions available
    doc_repo.get_versions_for_document = AsyncMock(return_value=[ver1])

    svc = DocumentService(session)
    svc._doc_repo = doc_repo

    with pytest.raises(DocumentVersionConflict) as exc:
        await svc.archive_version(ver1.id, admin_user)
    assert "Cannot archive the only active version" in str(exc.value)
