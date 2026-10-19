"""Billing Pydantic schemas."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_serializer


class BillingSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    policy_public_id: str
    status: str
    amount_due: Decimal
    currency: str
    due_date: Optional[date] = None
    last_paid_at: Optional[datetime] = None

    @field_serializer("amount_due")
    def serialize_decimal(self, v: Decimal) -> str:
        return str(v)


class BillingListResponse(BaseModel):
    items: List[BillingSummaryResponse]
