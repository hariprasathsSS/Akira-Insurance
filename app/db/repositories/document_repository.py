"""Document repository."""
from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.document import PolicyDocument, PolicyDocumentVersion


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_document_by_public_id(self, public_id: str) -> Optional[PolicyDocument]:
        result = await self._session.execute(
            select(PolicyDocument).where(PolicyDocument.public_id == public_id)
        )
        return result.scalar_one_or_none()

    async def get_document_by_id(self, doc_id: uuid.UUID) -> Optional[PolicyDocument]:
        result = await self._session.execute(
            select(PolicyDocument).where(PolicyDocument.id == doc_id)
        )
        return result.scalar_one_or_none()

    async def get_all_documents(
        self, limit: int = 20, offset: int = 0
    ) -> List[PolicyDocument]:
        result = await self._session.execute(
            select(PolicyDocument)
            .order_by(PolicyDocument.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create_document(self, doc: PolicyDocument) -> PolicyDocument:
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get_version_by_id(self, version_id: uuid.UUID) -> Optional[PolicyDocumentVersion]:
        result = await self._session.execute(
            select(PolicyDocumentVersion).where(PolicyDocumentVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_versions_for_document(
        self, document_id: uuid.UUID
    ) -> List[PolicyDocumentVersion]:
        result = await self._session.execute(
            select(PolicyDocumentVersion)
            .where(PolicyDocumentVersion.document_id == document_id)
            .order_by(PolicyDocumentVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def get_active_version(self, document_id: uuid.UUID) -> Optional[PolicyDocumentVersion]:
        result = await self._session.execute(
            select(PolicyDocumentVersion).where(
                PolicyDocumentVersion.document_id == document_id,
                PolicyDocumentVersion.is_active == True,  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def next_version_number(self, document_id: uuid.UUID) -> int:
        from sqlalchemy import func
        result = await self._session.execute(
            select(func.max(PolicyDocumentVersion.version_number)).where(
                PolicyDocumentVersion.document_id == document_id
            )
        )
        current = result.scalar_one_or_none()
        return (current or 0) + 1

    async def create_version(self, version: PolicyDocumentVersion) -> PolicyDocumentVersion:
        self._session.add(version)
        await self._session.flush()
        return version

    async def save_version(self, version: PolicyDocumentVersion) -> PolicyDocumentVersion:
        self._session.add(version)
        await self._session.flush()
        return version

    async def deactivate_all_versions(self, document_id: uuid.UUID) -> None:
        """Mark all existing active versions as superseded."""
        await self._session.execute(
            update(PolicyDocumentVersion)
            .where(
                PolicyDocumentVersion.document_id == document_id,
                PolicyDocumentVersion.is_active == True,  # noqa: E712
            )
            .values(is_active=False, status="superseded")
        )
