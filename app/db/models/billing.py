"""BillingRecord ORM model."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, DATE, NUMERIC, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BillingRecord(Base):
    __tablename__ = "billing_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False, index=True
    )
    premium_amount: Mapped[Decimal | None] = mapped_column(NUMERIC(12, 2), nullable=True)
    amount_due: Mapped[Decimal] = mapped_column(
        NUMERIC(12, 2), nullable=False, default=Decimal("0")
    )
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    due_date: Mapped[date | None] = mapped_column(DATE, nullable=True)
    last_paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    policy: Mapped["Policy"] = relationship("Policy", back_populates="billing_records")  # noqa: F821
