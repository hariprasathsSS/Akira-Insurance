"""Common Pydantic schemas."""
from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Dict[str, Any] = {}


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class PaginationMeta(BaseModel):
    total: Optional[int] = None
    limit: int
    offset: int
