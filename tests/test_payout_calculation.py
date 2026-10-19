"""Unit tests for deterministic Decimal payout calculation per Section 10 and 16."""
from __future__ import annotations

from decimal import Decimal
import pytest

from app.services.evaluation_service import calculate_payout


def test_standard_payout_calculation():
    """Estimate within limits with deductible."""
    estimate = Decimal("50000.00")
    deductible = Decimal("5000.00")
    limit = Decimal("500000.00")
    payout = calculate_payout(estimate, deductible, limit)
    # 50000 - 5000 = 45000
    assert payout == Decimal("45000.00")


def test_estimate_exceeds_limit():
    """Estimate greater than policy maximum coverage limit."""
    estimate = Decimal("600000.00")
    deductible = Decimal("5000.00")
    limit = Decimal("500000.00")
    payout = calculate_payout(estimate, deductible, limit)
    # min(600000, 500000) - 5000 = 495000
    assert payout == Decimal("495000.00")


def test_estimate_below_deductible_yields_zero():
    """Damage less than deductible yields 0 payout (never negative)."""
    estimate = Decimal("3000.00")
    deductible = Decimal("5000.00")
    limit = Decimal("500000.00")
    payout = calculate_payout(estimate, deductible, limit)
    assert payout == Decimal("0.00")


def test_zero_deductible():
    """Zero deductible policy (e.g., Gold motor or Pro health)."""
    estimate = Decimal("8500.00")
    deductible = Decimal("0.00")
    limit = Decimal("800000.00")
    payout = calculate_payout(estimate, deductible, limit)
    assert payout == Decimal("8500.00")


def test_with_approved_adjustments():
    """Deduction of non-covered items / salvage adjustments."""
    estimate = Decimal("100000.00")
    deductible = Decimal("10000.00")
    limit = Decimal("500000.00")
    adjustments = Decimal("15000.00")  # e.g., excluded consumables
    payout = calculate_payout(estimate, deductible, limit, approved_adjustments=adjustments)
    # 100000 - 10000 - 15000 = 75000
    assert payout == Decimal("75000.00")


def test_boundary_zero_estimate():
    """Zero estimate results in zero payout."""
    payout = calculate_payout(Decimal("0.00"), Decimal("5000.00"), Decimal("500000.00"))
    assert payout == Decimal("0.00")


def test_decimal_precision_cents():
    """Verify standard rounding to 2 decimal places."""
    estimate = Decimal("12345.678")
    deductible = Decimal("1000.00")
    limit = Decimal("100000.00")
    payout = calculate_payout(estimate, deductible, limit)
    assert payout == Decimal("11345.68")
