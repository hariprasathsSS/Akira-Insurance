"""Health check endpoints per Section 7.3."""
from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.rag.qdrant_store import check_qdrant_health

router = APIRouter(tags=["health"])


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def health_live() -> Dict[str, str]:
    """Liveness probe — returns 200 if the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Readiness probe — checks PostgreSQL and Qdrant connectivity.
    
    Returns 200 when required components are ready; 503 if DB or Qdrant unavailable.
    """
    settings = get_settings()

    # Check PostgreSQL
    db_ok = False
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # Check Qdrant
    qdrant_ok = check_qdrant_health()

    # Required dependencies: DB must be up. Qdrant is required for full operation.
    is_ready = db_ok and qdrant_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "database": "connected" if db_ok else "unavailable",
        "qdrant": "connected" if qdrant_ok else "unavailable",
        "dependencies": {
            "llm_configured": settings.llm_configured,
            "embedding_configured": settings.embedding_configured,
            "langfuse_configured": settings.langfuse_configured,
        },
    }
