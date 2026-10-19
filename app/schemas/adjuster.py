"""Adjuster note schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdjusterNoteCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note_text: str = Field(..., min_length=5, max_length=4000)


class AdjusterNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    claim_id: uuid.UUID
    note_type: str
    note_text: str
    created_at: datetime


class ClaimEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    force_re_evaluation: bool = False


class ValidationFlag(BaseModel):
    code: str
    severity: str = "review"  # review | block
    description: str


class PayoutBreakdown(BaseModel):
    model_config = ConfigDict(extra="allow")

    estimate_amount: Optional[str] = "0.00"
    deductible_applied: Optional[str] = "0.00"
    limit_applied: Optional[str] = "0.00"
    approved_adjustments: Optional[str] = "0.00"
    recommended_payout: Optional[str] = "0.00"
    formula: str = "max(0, min(estimate, limit) - deductible - adjustments)"
    note: Optional[str] = None
    flags: Optional[List[str]] = None


class ClaimEvaluationResponse(BaseModel):
    evaluation_id: uuid.UUID
    claim_public_id: str
    version: int
    extracted_facts: dict
    validation_flags: List[ValidationFlag]
    coverage_findings: dict
    calculation_breakdown: Dict[str, Any]
    recommended_payout: Optional[str] = None
    requires_human_review: bool
    evaluation_status: str
    trace_id: str = ""


class ClaimDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: str  # approved | denied | request_information
    decision_reason: str = Field(..., min_length=10)
    approved_amount: str = "0.00"
    evaluation_id: uuid.UUID


class ClaimDecisionResponse(BaseModel):
    decision_id: uuid.UUID
    claim_public_id: str
    decision: str
    approved_amount: str
    is_automated: bool
    created_at: datetime


class ClaimTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    to_status: str
    reason: Optional[str] = None


PayoutBreakdown.model_rebuild()
ClaimEvaluationResponse.model_rebuild()
