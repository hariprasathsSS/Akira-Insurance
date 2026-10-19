"""FastAPI application entrypoint for AKIRA INSURANCE."""
from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.v1.health import router as health_router
from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import get_engine, get_session_factory
from app.services.job_service import JobService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager: handles startup and graceful shutdown."""
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("Starting %s in %s mode...", settings.APP_NAME, settings.APP_ENV)

    # 1. Recover stuck background jobs from previous unexpected worker termination
    try:
        factory = get_session_factory()
        async with factory() as session:
            job_svc = JobService(session)
            recovered = await job_svc.mark_stuck_jobs_failed()
            await session.commit()
            if recovered > 0:
                logger.warning(
                    "Recovered %d orphaned jobs stuck in 'running' state from previous process run.",
                    recovered,
                )
    except Exception as exc:
        logger.warning("Could not run startup job recovery: %s", exc)

    # 2. Vector store collection check
    try:
        from app.rag.qdrant_store import check_qdrant_health, ensure_collection_exists
        if check_qdrant_health():
            ensure_collection_exists(
                collection_name=settings.QDRANT_COLLECTION,
                dense_dim=settings.effective_embedding_dim,
            )
            logger.info("Qdrant vector collection '%s' is ready.", settings.QDRANT_COLLECTION)
    except Exception as exc:
        logger.warning("Qdrant initialization deferred: %s", exc)

    yield

    # Shutdown: cleanly close database connection pool
    logger.info("Shutting down %s...", settings.APP_NAME)
    engine = get_engine()
    await engine.dispose()
    logger.info("Database connection pool closed.")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensure every HTTP request and response carries an X-Request-ID header."""

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title="AKIRA INSURANCE Backend API",
        description=(
            "Enterprise-style insurance claims AI backend API with LangGraph "
            "agent orchestration, Langfuse observability, Qdrant hybrid RAG, "
            "and deterministic claim evaluation."
        ),
        version="0.1.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # Request ID
    app.add_middleware(RequestIDMiddleware)

    # Global Error Handlers
    register_error_handlers(app)

    # Health checks at root level
    app.include_router(health_router)

    # Main API router under configured prefix (default /api/v1)
    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    return app


app = create_application()
