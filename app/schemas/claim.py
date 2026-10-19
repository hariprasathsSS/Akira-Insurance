"""Claim Pydantic schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class ClaimCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    policy_public_id: str
    incident_type: str = Field(..., min_length=2, max_length=80)
    incident_date: date
    incident_location: Optional[str] = Field(None, max_length=255)
    incident_description: str = Field(..., min_length=10)
    requested_amount: Decimal = Field(..., ge=Decimal("0"))
    idempotency_key: str = Field(..., min_length=8, max_length=255)

    @field_validator("requested_amount")
    @classmethod
    def amount_must_be_nonnegative(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("requested_amount must be non-negative")
        return v


class ClaimSubmitRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confirmation: bool = True


class ClaimResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    policy_public_id: str = ""
    status: str
    incident_type: Optional[str] = None
    incident_date: Optional[date] = None
    incident_location: Optional[str] = None
    incident_description: Optional[str] = None
    requested_amount: Optional[Decimal] = None
    recommended_payout: Optional[Decimal] = None
    approved_payout: Optional[Decimal] = None
    fraud_flagged: bool
    submitted_at: Optional[datetime] = None
    decided_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("requested_amount", "recommended_payout", "approved_payout")
    def serialize_optional_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return str(v) if v is not None else None


class ClaimListResponse(BaseModel):
    items: List[ClaimResponse]
    total: int


class ClaimEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_status: Optional[str] = None
    to_status: str
    reason: Optional[str] = None
    created_at: datetime
