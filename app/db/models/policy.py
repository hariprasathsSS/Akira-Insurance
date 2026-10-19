"""Policy ORM model."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CHAR,
    DATE,
    NUMERIC,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    plan_name: Mapped[str] = mapped_column(String(160), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR")
    deductible: Mapped[Decimal] = mapped_column(NUMERIC(12, 2), nullable=False, default=Decimal("0"))
    max_coverage: Mapped[Decimal] = mapped_column(NUMERIC(14, 2), nullable=False)
    policy_number: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(DATE, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(DATE, nullable=True)
    current_document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policy_document_versions.id", use_alter=True, name="fk_policy_current_docver"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="policies")  # noqa: F821
    billing_records: Mapped[list["BillingRecord"]] = relationship(  # noqa: F821
        "BillingRecord", back_populates="policy", lazy="select"
    )
    claims: Mapped[list["Claim"]] = relationship(  # noqa: F821
        "Claim", back_populates="policy", lazy="select"
    )
