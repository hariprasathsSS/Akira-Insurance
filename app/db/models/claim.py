"""Claim-related ORM models."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DATE,
    NUMERIC,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    incident_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    incident_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    incident_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incident_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_amount: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    adjuster_notes_latest: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_payout: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    approved_payout: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    fraud_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    policy: Mapped["Policy"] = relationship("Policy", back_populates="claims")  # noqa: F821
    notes: Mapped[list["ClaimNote"]] = relationship(
        "ClaimNote", back_populates="claim", lazy="select"
    )
    evaluations: Mapped[list["ClaimEvaluation"]] = relationship(
        "ClaimEvaluation", back_populates="claim", lazy="select"
    )
    decisions: Mapped[list["ClaimDecision"]] = relationship(
        "ClaimDecision", back_populates="claim", lazy="select"
    )
    events: Mapped[list["ClaimEvent"]] = relationship(
        "ClaimEvent", back_populates="claim", lazy="select"
    )


class ClaimNote(Base):
    __tablename__ = "claim_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    note_text: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(24), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="notes")


class ClaimEvaluation(Base):
    __tablename__ = "claim_evaluations"
    __table_args__ = (UniqueConstraint("claim_id", "version", name="uq_claim_evaluation_version"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    extracted_facts: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    validation_flags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    coverage_findings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estimate_amount: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    deductible_applied: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    limit_applied: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    recommended_payout: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    calculation_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    evaluation_status: Mapped[str] = mapped_column(String(24), nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="evaluations")


class ClaimDecision(Base):
    __tablename__ = "claim_decisions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claim_evaluations.id"), nullable=True
    )
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    decision_reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    approved_amount: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="decisions")


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    claim: Mapped["Claim"] = relationship("Claim", back_populates="events")
