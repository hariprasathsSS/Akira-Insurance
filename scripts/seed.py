"""Idempotent database seed script per Section 6.

Creates standard demo personas, policies, billing records, sample claims,
and policy document families. Safe to run repeatedly without creating duplicates.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import (
    CLAIM_STATUS_EVALUATED,
    CLAIM_STATUS_SUBMITTED,
    CLAIM_STATUS_UNDER_REVIEW,
    POLICY_STATUS_ACTIVE,
    POLICY_STATUS_GRACE,
    POLICY_TYPE_HEALTH,
    POLICY_TYPE_HOME,
    POLICY_TYPE_MOTOR,
    ROLE_ADMIN,
    ROLE_ADJUSTER,
    ROLE_CUSTOMER,
)
from app.db.models.billing import BillingRecord
from app.db.models.claim import Claim, ClaimEvent
from app.db.models.document import PolicyDocument
from app.db.models.policy import Policy
from app.db.models.user import User
from app.db.session import get_session_factory
from scripts.generate_sample_pdfs import generate_sample_pdfs


# ── Seed Data Definitions ─────────────────────────────────────────────────────

USERS = [
    {
        "public_id": "U-101",
        "name": "Rahul Desai",
        "email": "rahul.desai@example.test",
        "role": ROLE_CUSTOMER,
    },
    {
        "public_id": "U-102",
        "name": "Priya Sharma",
        "email": "priya.sharma@example.test",
        "role": ROLE_CUSTOMER,
    },
    {
        "public_id": "U-103",
        "name": "Amit Patel",
        "email": "amit.patel@example.test",
        "role": ROLE_CUSTOMER,
    },
    {
        "public_id": "U-104",
        "name": "Neha Gupta",
        "email": "neha.gupta@example.test",
        "role": ROLE_CUSTOMER,
    },
    {
        "public_id": "U-900",
        "name": "Vikram Singh",
        "email": "vikram.singh@example.test",
        "role": ROLE_ADJUSTER,
    },
    {
        "public_id": "U-901",
        "name": "Akira Admin",
        "email": "admin@akira.example.test",
        "role": ROLE_ADMIN,
    },
]

POLICIES = [
    {
        "public_id": "POL-101",
        "user_public_id": "U-101",
        "policy_number": "POL-HLT-2026-00101",
        "plan_name": "Health Guard Basic",
        "policy_type": POLICY_TYPE_HEALTH,
        "plan_tier": "basic",
        "status": POLICY_STATUS_ACTIVE,
        "currency": "INR",
        "deductible": Decimal("5000.00"),
        "max_coverage": Decimal("500000.00"),
        "billing_status": "paid",
        "amount_due": Decimal("0.00"),
    },
    {
        "public_id": "POL-102",
        "user_public_id": "U-102",
        "policy_number": "POL-HLT-2026-00102",
        "plan_name": "Health Shield Pro",
        "policy_type": POLICY_TYPE_HEALTH,
        "plan_tier": "pro",
        "status": POLICY_STATUS_GRACE,
        "currency": "INR",
        "deductible": Decimal("0.00"),
        "max_coverage": Decimal("1500000.00"),
        "billing_status": "due",
        "amount_due": Decimal("12500.00"),
    },
    {
        "public_id": "POL-103",
        "user_public_id": "U-103",
        "policy_number": "POL-MOT-2026-00103",
        "plan_name": "Motor DriveCare Gold",
        "policy_type": POLICY_TYPE_MOTOR,
        "plan_tier": "gold",
        "status": POLICY_STATUS_ACTIVE,
        "currency": "INR",
        "deductible": Decimal("0.00"),
        "max_coverage": Decimal("800000.00"),
        "billing_status": "paid",
        "amount_due": Decimal("0.00"),
    },
    {
        "public_id": "POL-104",
        "user_public_id": "U-104",
        "policy_number": "POL-HOM-2026-00104",
        "plan_name": "Home Protect Elite",
        "policy_type": POLICY_TYPE_HOME,
        "plan_tier": "elite",
        "status": POLICY_STATUS_ACTIVE,
        "currency": "INR",
        "deductible": Decimal("10000.00"),
        "max_coverage": Decimal("5000000.00"),
        "billing_status": "paid",
        "amount_due": Decimal("0.00"),
    },
]

SAMPLE_CLAIMS = [
    {
        "public_id": "CLM-20261001-001",
        "policy_public_id": "POL-101",
        "user_public_id": "U-101",
        "status": CLAIM_STATUS_SUBMITTED,
        "incident_type": "inpatient_hospitalization",
        "incident_date": date(2026, 9, 15),
        "incident_location": "Apollo Hospital, Mumbai",
        "incident_description": "SYNTHETIC: 3-day hospitalization for acute appendectomy and recovery.",
        "requested_amount": Decimal("35000.00"),
        "idempotency_key": "seed-claim-rahul-001",
    },
    {
        "public_id": "CLM-20261001-002",
        "policy_public_id": "POL-103",
        "user_public_id": "U-103",
        "status": CLAIM_STATUS_EVALUATED,
        "incident_type": "collision",
        "incident_date": date(2026, 9, 20),
        "incident_location": "MG Road, Bengaluru",
        "incident_description": "SYNTHETIC: Low-speed rear bumper collision; plastic bumper replacement.",
        "requested_amount": Decimal("8500.00"),
        "recommended_payout": Decimal("8500.00"),
        "idempotency_key": "seed-claim-amit-001",
    },
    {
        "public_id": "CLM-20261001-003",
        "policy_public_id": "POL-104",
        "user_public_id": "U-104",
        "status": CLAIM_STATUS_UNDER_REVIEW,
        "incident_type": "water_damage",
        "incident_date": date(2026, 10, 2),
        "incident_location": "Residence, Delhi NCR",
        "incident_description": "SYNTHETIC: Burst bathroom pipe resulting in flooring and drywall damage.",
        "requested_amount": Decimal("75000.00"),
        "idempotency_key": "seed-claim-neha-001",
    },
]

DOCUMENT_FAMILIES = [
    {
        "public_id": "DOC-HEALTH-001",
        "policy_type": POLICY_TYPE_HEALTH,
        "plan_tier": "basic",
        "title": "Health Guard Basic Policy Document",
        "description": "Standard terms and conditions for Health Guard Basic plan.",
    },
    {
        "public_id": "DOC-MOTOR-001",
        "policy_type": POLICY_TYPE_MOTOR,
        "plan_tier": "gold",
        "title": "Motor DriveCare Gold Comprehensive Policy",
        "description": "Comprehensive private car insurance with zero depreciation endorsement.",
    },
    {
        "public_id": "DOC-HOME-001",
        "policy_type": POLICY_TYPE_HOME,
        "plan_tier": "elite",
        "title": "Home Protect Elite Comprehensive Policy",
        "description": "Structure and contents coverage for residential properties.",
    },
]


async def seed_database() -> None:
    """Run idempotent seeding for all entities."""
    factory = get_session_factory()
    now = datetime.now(timezone.utc)

    async with factory() as session:
        # ── 1. Seed Users ─────────────────────────────────────────────────────
        user_map: dict[str, User] = {}
        for u_data in USERS:
            res = await session.execute(
                select(User).where(User.public_id == u_data["public_id"])
            )
            user = res.scalar_one_or_none()
            if not user:
                user = User(
                    id=uuid.uuid4(),
                    public_id=u_data["public_id"],
                    name=u_data["name"],
                    email=u_data["email"],
                    role=u_data["role"],
                    is_active=True,
                )
                session.add(user)
                await session.flush()
                print(f"Created user: {user.public_id} ({user.name})")
            user_map[user.public_id] = user

        # ── 2. Seed Policies & Billing ────────────────────────────────────────
        policy_map: dict[str, Policy] = {}
        for p_data in POLICIES:
            owner = user_map[p_data["user_public_id"]]
            res = await session.execute(
                select(Policy).where(Policy.public_id == p_data["public_id"])
            )
            policy = res.scalar_one_or_none()
            if not policy:
                policy = Policy(
                    id=uuid.uuid4(),
                    public_id=p_data["public_id"],
                    user_id=owner.id,
                    policy_number=p_data["policy_number"],
                    plan_name=p_data["plan_name"],
                    policy_type=p_data["policy_type"],
                    plan_tier=p_data["plan_tier"],
                    status=p_data["status"],
                    currency=p_data["currency"],
                    deductible=p_data["deductible"],
                    max_coverage=p_data["max_coverage"],
                )
                session.add(policy)
                await session.flush()
                print(f"Created policy: {policy.public_id} ({policy.plan_name})")

                # Create matching billing record
                billing = BillingRecord(
                    id=uuid.uuid4(),
                    policy_id=policy.id,
                    amount_due=p_data["amount_due"],
                    currency=p_data["currency"],
                    status=p_data["billing_status"],
                    due_date=date(2026, 11, 1) if p_data["billing_status"] == "due" else None,
                    last_paid_at=now if p_data["billing_status"] == "paid" else None,
                )
                session.add(billing)
                await session.flush()
                print(f"Created billing for policy {policy.public_id}: {billing.status}")
            policy_map[policy.public_id] = policy

        # ── 3. Seed Sample Claims ─────────────────────────────────────────────
        for c_data in SAMPLE_CLAIMS:
            res = await session.execute(
                select(Claim).where(Claim.public_id == c_data["public_id"])
            )
            claim = res.scalar_one_or_none()
            if not claim:
                owner = user_map[c_data["user_public_id"]]
                policy = policy_map[c_data["policy_public_id"]]
                claim = Claim(
                    id=uuid.uuid4(),
                    public_id=c_data["public_id"],
                    policy_id=policy.id,
                    created_by_user_id=owner.id,
                    status=c_data["status"],
                    incident_type=c_data["incident_type"],
                    incident_date=c_data["incident_date"],
                    incident_location=c_data["incident_location"],
                    incident_description=c_data["incident_description"],
                    requested_amount=c_data["requested_amount"],
                    recommended_payout=c_data.get("recommended_payout"),
                    idempotency_key=c_data["idempotency_key"],
                    submitted_at=now,
                )
                session.add(claim)
                await session.flush()

                event = ClaimEvent(
                    id=uuid.uuid4(),
                    claim_id=claim.id,
                    from_status=None,
                    to_status=claim.status,
                    actor_user_id=owner.id,
                    reason="Seeded sample claim",
                )
                session.add(event)
                await session.flush()
                print(f"Created sample claim: {claim.public_id} ({claim.status})")

        # ── 4. Seed Document Families ─────────────────────────────────────────
        admin_user = user_map["U-901"]
        for d_data in DOCUMENT_FAMILIES:
            res = await session.execute(
                select(PolicyDocument).where(PolicyDocument.public_id == d_data["public_id"])
            )
            doc = res.scalar_one_or_none()
            if not doc:
                doc = PolicyDocument(
                    id=uuid.uuid4(),
                    public_id=d_data["public_id"],
                    policy_type=d_data["policy_type"],
                    plan_tier=d_data["plan_tier"],
                    title=d_data["title"],
                    description=d_data["description"],
                    created_by_user_id=admin_user.id,
                )
                session.add(doc)
                await session.flush()
                print(f"Created document family: {doc.public_id} ({doc.title})")

        await session.commit()
        print("Idempotent database seeding completed successfully.")

    # ── 5. Generate sample policy PDFs on disk ────────────────────────────────
    storage_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "storage", "sample_policies"
    )
    generate_sample_pdfs(storage_dir)


if __name__ == "__main__":
    asyncio.run(seed_database())
