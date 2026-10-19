"""Domain exception types for AKIRA INSURANCE."""
from __future__ import annotations

from typing import Any, Dict, Optional


class AkiraBaseError(Exception):
    """Base for all domain errors."""

    code: str = "INTERNAL_ERROR"
    http_status: int = 500

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if code:
            self.code = code


class AuthRequired(AkiraBaseError):
    code = "AUTH_REQUIRED"
    http_status = 401


class DemoAuthDisabled(AkiraBaseError):
    code = "DEMO_AUTH_DISABLED"
    http_status = 403


class Forbidden(AkiraBaseError):
    code = "FORBIDDEN"
    http_status = 403


class ResourceNotFound(AkiraBaseError):
    code = "RESOURCE_NOT_FOUND"
    http_status = 404


class ValidationError(AkiraBaseError):
    code = "VALIDATION_ERROR"
    http_status = 422


class LLMNotConfigured(AkiraBaseError):
    code = "LLM_NOT_CONFIGURED"
    http_status = 503


class LLMProviderError(AkiraBaseError):
    code = "LLM_PROVIDER_ERROR"
    http_status = 502


class RAGNotReady(AkiraBaseError):
    code = "RAG_NOT_READY"
    http_status = 503


class DocumentInvalid(AkiraBaseError):
    code = "DOCUMENT_INVALID"
    http_status = 422


class DocumentVersionConflict(AkiraBaseError):
    code = "DOCUMENT_VERSION_CONFLICT"
    http_status = 409


class IngestionFailed(AkiraBaseError):
    code = "INGESTION_FAILED"
    http_status = 500


class ClaimStateConflict(AkiraBaseError):
    code = "CLAIM_STATE_CONFLICT"
    http_status = 409


class IdempotencyConflict(AkiraBaseError):
    code = "IDEMPOTENCY_CONFLICT"
    http_status = 409


class CoverageUncertain(AkiraBaseError):
    code = "COVERAGE_UNCERTAIN"
    http_status = 422


class EvaluationFailed(AkiraBaseError):
    code = "EVALUATION_FAILED"
    http_status = 500
