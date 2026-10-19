"""Unit tests for the claim lifecycle state machine per Section 10 and 16."""
from __future__ import annotations

import pytest

from app.core.constants import (
    CLAIM_STATUS_APPROVED,
    CLAIM_STATUS_CLOSED,
    CLAIM_STATUS_DENIED,
    CLAIM_STATUS_DRAFT,
    CLAIM_STATUS_EVALUATED,
    CLAIM_STATUS_NEEDS_INFORMATION,
    CLAIM_STATUS_PENDING_APPROVAL,
    CLAIM_STATUS_SUBMITTED,
    CLAIM_STATUS_UNDER_REVIEW,
    CLAIM_TRANSITIONS,
)
from app.core.exceptions import ClaimStateConflict
from app.services.claim_service import _assert_valid_transition


def test_valid_transitions_from_draft():
    """Draft may only transition to submitted."""
    _assert_valid_transition(CLAIM_STATUS_DRAFT, CLAIM_STATUS_SUBMITTED)


def test_valid_transitions_from_submitted():
    """Submitted may transition to under_review or needs_information."""
    _assert_valid_transition(CLAIM_STATUS_SUBMITTED, CLAIM_STATUS_UNDER_REVIEW)
    _assert_valid_transition(CLAIM_STATUS_SUBMITTED, CLAIM_STATUS_NEEDS_INFORMATION)


def test_valid_transitions_from_under_review():
    """Under review may transition to needs_information or evaluated."""
    _assert_valid_transition(CLAIM_STATUS_UNDER_REVIEW, CLAIM_STATUS_NEEDS_INFORMATION)
    _assert_valid_transition(CLAIM_STATUS_UNDER_REVIEW, CLAIM_STATUS_EVALUATED)


def test_valid_transitions_from_evaluated():
    """Evaluated may transition to pending_approval, approved, or denied."""
    _assert_valid_transition(CLAIM_STATUS_EVALUATED, CLAIM_STATUS_PENDING_APPROVAL)
    _assert_valid_transition(CLAIM_STATUS_EVALUATED, CLAIM_STATUS_APPROVED)
    _assert_valid_transition(CLAIM_STATUS_EVALUATED, CLAIM_STATUS_DENIED)


def test_valid_transitions_to_closed():
    """Approved and denied may transition to closed."""
    _assert_valid_transition(CLAIM_STATUS_APPROVED, CLAIM_STATUS_CLOSED)
    _assert_valid_transition(CLAIM_STATUS_DENIED, CLAIM_STATUS_CLOSED)


def test_invalid_transition_draft_to_approved():
    """Direct approval from draft is strictly prohibited."""
    with pytest.raises(ClaimStateConflict) as exc:
        _assert_valid_transition(CLAIM_STATUS_DRAFT, CLAIM_STATUS_APPROVED)
    assert "cannot transition from 'draft' to 'approved'" in str(exc.value)


def test_invalid_transition_submitted_to_approved():
    """Submitted claims cannot bypass review/evaluation to approved."""
    with pytest.raises(ClaimStateConflict):
        _assert_valid_transition(CLAIM_STATUS_SUBMITTED, CLAIM_STATUS_APPROVED)


def test_invalid_transition_from_closed():
    """Closed claims are terminal and cannot transition anywhere."""
    with pytest.raises(ClaimStateConflict):
        _assert_valid_transition(CLAIM_STATUS_CLOSED, CLAIM_STATUS_SUBMITTED)
    with pytest.raises(ClaimStateConflict):
        _assert_valid_transition(CLAIM_STATUS_CLOSED, CLAIM_STATUS_UNDER_REVIEW)


def test_state_transitions_matrix_completeness():
    """Ensure all declared states exist in transitions map."""
    all_states = {
        CLAIM_STATUS_DRAFT,
        CLAIM_STATUS_SUBMITTED,
        CLAIM_STATUS_UNDER_REVIEW,
        CLAIM_STATUS_NEEDS_INFORMATION,
        CLAIM_STATUS_EVALUATED,
        CLAIM_STATUS_PENDING_APPROVAL,
        CLAIM_STATUS_APPROVED,
        CLAIM_STATUS_DENIED,
        CLAIM_STATUS_CLOSED,
    }
    assert set(CLAIM_TRANSITIONS.keys()) == all_states
