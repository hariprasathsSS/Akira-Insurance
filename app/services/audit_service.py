"""Audit service — appends audit log entries."""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.audit import AuditLog
from app.db.repositories.job_repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditRepository(session)

    async def log(
        self,
        action: str,
        resource_type: str,
        outcome: str,
        actor_user_id: Optional[uuid.UUID] = None,
        resource_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        # Sanitize — do not log raw credentials, prompt content, or full PII
        safe_details = details or {}
        entry = AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            outcome=outcome,
            details=safe_details,
        )
        return await self._repo.create(entry)
