"""Unit tests for Straight-Through Processing (STP) auto-approval gate per Section 10 and 16."""
from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.core.constants import CLAIM_STATUS_APPROVED, CLAIM_STATUS_PENDING_APPROVAL
from app.db.models.claim import Claim, ClaimEvaluation
from app.db.models.policy import Policy
from app.services.approval_service import ApprovalService


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def base_claim():
    return Claim(
        id=uuid.uuid4(),
        public_id="CLM-TEST-001",
        policy_id=uuid.uuid4(),
        created_by_user_id=uuid.uuid4(),
        status=CLAIM_STATUS_PENDING_APPROVAL,
        incident_type="minor_scratch",
        incident_date=date(2026, 10, 1),
        incident_description="Minor bumper scratch during parking.",
        requested_amount=Decimal("5000.00"),
        fraud_flagged=False,
    )


@pytest.fixture
def base_policy():
    return Policy(
        id=uuid.uuid4(),
        public_id="POL-TEST-001",
        user_id=uuid.uuid4(),
        status="active",
        deductible=Decimal("0.00"),
        max_coverage=Decimal("500000.00"),
    )


@pytest.mark.asyncio
async def test_stp_eligible_below_threshold(mock_session, base_claim, base_policy):
    """Claim with payout < ₹10,000 and clean evaluation is auto-approved."""
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("8500.00"),
        validation_flags=[],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is True
    assert base_claim.status == CLAIM_STATUS_APPROVED
    assert base_claim.approved_payout == Decimal("8500.00")


@pytest.mark.asyncio
async def test_stp_blocked_at_exact_threshold(mock_session, base_claim, base_policy):
    """Payout exactly equal to ₹10,000 threshold must NOT be auto-approved."""
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("10000.00"),
        validation_flags=[],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is False
    assert base_claim.status == CLAIM_STATUS_PENDING_APPROVAL


@pytest.mark.asyncio
async def test_stp_blocked_above_threshold(mock_session, base_claim, base_policy):
    """Payout above threshold requires human adjuster review."""
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("45000.00"),
        validation_flags=[],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is False
    assert base_claim.status == CLAIM_STATUS_PENDING_APPROVAL


@pytest.mark.asyncio
async def test_stp_blocked_by_validation_flags(mock_session, base_claim, base_policy):
    """Presence of any validation flag blocks STP even if amount is small."""
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("3000.00"),
        validation_flags=[{"code": "FREQUENT_CLAIMS_REVIEW", "severity": "review"}],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is False


@pytest.mark.asyncio
async def test_stp_blocked_on_inactive_policy(mock_session, base_claim, base_policy):
    """Policy in grace_period or lapsed status blocks auto-approval."""
    base_policy.status = "grace_period"
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("4000.00"),
        validation_flags=[],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is False


@pytest.mark.asyncio
async def test_stp_blocked_by_fraud_flag(mock_session, base_claim, base_policy):
    """Fraud flagged claim cannot be auto-approved under any circumstances."""
    base_claim.fraud_flagged = True
    svc = ApprovalService(mock_session)
    evaluation = ClaimEvaluation(
        id=uuid.uuid4(),
        claim_id=base_claim.id,
        version=1,
        evaluation_status="succeeded",
        recommended_payout=Decimal("1500.00"),
        validation_flags=[],
    )

    eligible = await svc.attempt_stp(base_claim, evaluation, base_policy)
    assert eligible is False
