"""Document Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PolicyDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    public_id: str
    policy_type: str
    plan_tier: str
    title: str
    description: Optional[str] = None
    created_at: datetime


class PolicyDocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    version_number: int
    original_filename: str
    sha256: str
    mime_type: str
    file_size_bytes: int
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    status: str
    is_active: bool
    qdrant_collection: str
    ingestion_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirm: bool = True


class PolicyDocumentListResponse(BaseModel):
    items: List[PolicyDocumentResponse]
    total: int


class PolicyDocumentVersionListResponse(BaseModel):
    items: List[PolicyDocumentVersionResponse]
    total: int


class DocumentUploadResponse(BaseModel):
    document: PolicyDocumentResponse
    version: PolicyDocumentVersionResponse
    job_public_id: str
    message: str = "Document uploaded. Ingestion job started in background."
