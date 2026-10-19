"""Admin metrics and operational telemetry endpoints per Section 7.3."""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.core.config import get_settings
from app.db.models.claim import Claim, ClaimDecision, ClaimEvaluation
from app.db.models.document import PolicyDocument, PolicyDocumentVersion
from app.db.models.job import BackgroundJob
from app.db.models.policy import Policy
from app.db.models.user import User

router = APIRouter(prefix="/admin", tags=["admin-metrics"])


@router.get("/metrics")
async def get_metrics(
    user: User = Depends(require_admin),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Admin: return operational counts and system statistics from the application database."""
    settings = get_settings()

    # Query counts from DB
    users_count = (await session.execute(select(func.count(User.id)))).scalar_one()
    policies_count = (await session.execute(select(func.count(Policy.id)))).scalar_one()
    claims_total = (await session.execute(select(func.count(Claim.id)))).scalar_one()

    # Claims grouped by status
    claims_by_status_raw = (
        await session.execute(
            select(Claim.status, func.count(Claim.id)).group_by(Claim.status)
        )
    ).all()
    claims_by_status = {status: count for status, count in claims_by_status_raw}

    # Decisions count (automated vs manual)
    decisions_total = (
        await session.execute(select(func.count(ClaimDecision.id)))
    ).scalar_one()
    auto_decisions = (
        await session.execute(
            select(func.count(ClaimDecision.id)).where(ClaimDecision.is_automated == True)  # noqa: E712
        )
    ).scalar_one()

    # Evaluations count
    evaluations_total = (
        await session.execute(select(func.count(ClaimEvaluation.id)))
    ).scalar_one()

    # Documents and versions
    doc_families = (
        await session.execute(select(func.count(PolicyDocument.id)))
    ).scalar_one()
    active_versions = (
        await session.execute(
            select(func.count(PolicyDocumentVersion.id)).where(
                PolicyDocumentVersion.is_active == True  # noqa: E712
            )
        )
    ).scalar_one()

    # Background jobs summary
    jobs_by_status_raw = (
        await session.execute(
            select(BackgroundJob.status, func.count(BackgroundJob.id)).group_by(
                BackgroundJob.status
            )
        )
    ).all()
    jobs_by_status = {status: count for status, count in jobs_by_status_raw}

    # Safe Langfuse dashboard URL
    langfuse_url = settings.LANGFUSE_HOST if settings.langfuse_configured else None

    return {
        "users": {"total": users_count},
        "policies": {"total": policies_count},
        "claims": {
            "total": claims_total,
            "by_status": claims_by_status,
            "evaluations_count": evaluations_total,
            "decisions_count": decisions_total,
            "stp_auto_approved_count": auto_decisions,
        },
        "documents": {
            "families_count": doc_families,
            "active_versions_count": active_versions,
        },
        "jobs": {
            "by_status": jobs_by_status,
        },
        "observability": {
            "langfuse_enabled": settings.langfuse_configured,
            "langfuse_dashboard_url": langfuse_url,
        },
    }
