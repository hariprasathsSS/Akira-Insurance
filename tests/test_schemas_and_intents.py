"""Unit tests for Pydantic schemas and deterministic intent classification per Section 9, 15, and 16."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
import pydantic
import pytest

from app.agents.intents import classify_intent_deterministic
from app.core.constants import (
    INTENT_CHECK_CLAIM_STATUS,
    INTENT_CHECK_PAYMENT_STATUS,
    INTENT_CHECK_PLAN_DETAILS,
    INTENT_LODGE_CLAIM_FNOL,
    INTENT_POLICY_RAG_QUERY,
    INTENT_UNKNOWN,
)
from app.schemas.adjuster import AdjusterNoteCreateRequest, ClaimDecisionRequest
from app.schemas.chat import ChatRequest
from app.schemas.claim import ClaimCreateRequest


def test_classify_intent_plan_details():
    assert classify_intent_deterministic("What is my deductible?") == INTENT_CHECK_PLAN_DETAILS
    assert classify_intent_deterministic("Show me my coverage limit") == INTENT_CHECK_PLAN_DETAILS


def test_classify_intent_billing():
    assert classify_intent_deterministic("How much premium do I owe?") == INTENT_CHECK_PAYMENT_STATUS
    assert classify_intent_deterministic("Check my bill status") == INTENT_CHECK_PAYMENT_STATUS


def test_classify_intent_claim_status():
    assert classify_intent_deterministic("What is the status of my claim?") == INTENT_CHECK_CLAIM_STATUS
    assert classify_intent_deterministic("Has my claim been approved?") == INTENT_CHECK_CLAIM_STATUS


def test_classify_intent_fnol():
    assert classify_intent_deterministic("I want to file a new claim for an accident") == INTENT_LODGE_CLAIM_FNOL
    assert classify_intent_deterministic("How do I report damage to file claim?") == INTENT_LODGE_CLAIM_FNOL


def test_classify_intent_rag_query():
    assert classify_intent_deterministic("Does my policy cover flood damage?") == INTENT_POLICY_RAG_QUERY
    assert classify_intent_deterministic("Are cosmetic surgeries excluded?") == INTENT_POLICY_RAG_QUERY


def test_classify_intent_unknown():
    assert classify_intent_deterministic("What is the weather in Paris?") is None


def test_claim_create_request_validation_success():
    req = ClaimCreateRequest(
        policy_public_id="POL-101",
        incident_type="accident",
        incident_date=date(2026, 10, 1),
        incident_location="Bengaluru",
        incident_description="Minor front bumper impact with pillar.",
        requested_amount=Decimal("15000.00"),
        idempotency_key="unique-client-key-12345",
    )
    assert req.requested_amount == Decimal("15000.00")
    assert req.policy_public_id == "POL-101"


def test_claim_create_request_negative_amount_fails():
    with pytest.raises(pydantic.ValidationError):
        ClaimCreateRequest(
            policy_public_id="POL-101",
            incident_type="accident",
            incident_date=date(2026, 10, 1),
            incident_description="Sample incident",
            requested_amount=Decimal("-100.00"),
            idempotency_key="valid-key-123",
        )


def test_claim_create_request_short_idempotency_key_fails():
    with pytest.raises(pydantic.ValidationError):
        ClaimCreateRequest(
            policy_public_id="POL-101",
            incident_type="accident",
            incident_date=date(2026, 10, 1),
            incident_description="Sample incident description",
            requested_amount=Decimal("5000.00"),
            idempotency_key="short",  # min_length is 8
        )


def test_adjuster_note_validation():
    with pytest.raises(pydantic.ValidationError):
        AdjusterNoteCreateRequest(note_text="no")  # min_length 5

    valid = AdjusterNoteCreateRequest(note_text="Reviewed medical bills.")
    assert valid.note_text == "Reviewed medical bills."


def test_claim_decision_validation():
    with pytest.raises(pydantic.ValidationError):
        import uuid
        ClaimDecisionRequest(
            decision="approved",
            decision_reason="too short",  # min_length 10
            evaluation_id=uuid.uuid4(),
        )
