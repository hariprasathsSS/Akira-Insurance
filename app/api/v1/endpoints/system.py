"""System and health check endpoints."""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.rag.qdrant_store import check_qdrant_health

router = APIRouter()


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """Check database and vector store health."""
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    qdrant_ok = check_qdrant_health()
    overall = "ok" if db_ok and qdrant_ok else ("degraded" if db_ok else "unhealthy")

    return {
        "status": overall,
        "database": "connected" if db_ok else "disconnected",
        "qdrant": "connected" if qdrant_ok else "unavailable",
    }


@router.get("/system/info")
async def system_info() -> Dict[str, Any]:
    """Return runtime configuration state (anonymized/safe)."""
    settings = get_settings()
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "demo_auth_active": settings.demo_auth_active,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_configured": settings.llm_configured,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_configured": settings.embedding_configured,
        "langfuse_enabled": settings.langfuse_configured,
        "stp_threshold_inr": settings.STP_THRESHOLD_INR,
    }
