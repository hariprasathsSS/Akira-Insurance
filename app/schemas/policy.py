"""Policy Pydantic schemas."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class PolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    public_id: str
    plan_name: str
    policy_type: str
    plan_tier: str
    status: str
    currency: str
    deductible: Decimal
    max_coverage: Decimal
    policy_number: str
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None

    @field_serializer("deductible", "max_coverage")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


class PolicyListResponse(BaseModel):
    items: List[PolicyResponse]
    total: int
