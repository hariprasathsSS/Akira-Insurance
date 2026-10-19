"""Global error handlers and request ID tracking for AKIRA INSURANCE."""
from __future__ import annotations

import logging
import uuid
from typing import Any
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AkiraBaseError

logger = logging.getLogger(__name__)


def get_request_id(request: Request) -> str:
    """Extract or generate a request ID."""
    req_id = getattr(request.state, "request_id", None)
    if not req_id:
        req_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        request.state.request_id = req_id
    return req_id


def register_error_handlers(app: FastAPI) -> None:
    """Attach domain exception and validation error handlers to FastAPI application."""

    @app.exception_handler(AkiraBaseError)
    async def handle_akira_error(request: Request, exc: AkiraBaseError) -> JSONResponse:
        req_id = get_request_id(request)
        logger.warning(
            "Akira domain error: code=%s http_status=%d request_id=%s message=%s",
            exc.code,
            exc.http_status,
            req_id,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "request_id": req_id,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_request_id(request)
        errors = exc.errors()
        logger.info(
            "Request validation error: request_id=%s count=%d", req_id, len(errors)
        )
        # Format details without exposing sensitive internals
        details: dict[str, Any] = {
            "fields": [
                {
                    "loc": [str(loc) for loc in err.get("loc", [])],
                    "msg": err.get("msg", ""),
                    "type": err.get("type", ""),
                }
                for err in errors
            ]
        }
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "The request body or parameters failed validation.",
                    "request_id": req_id,
                    "details": details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        req_id = get_request_id(request)
        logger.exception("Unhandled server exception: request_id=%s", req_id)
        # Never leak stack trace or internal SQL/secrets to client
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal server error occurred. Please contact support.",
                    "request_id": req_id,
                    "details": {},
                }
            },
        )
