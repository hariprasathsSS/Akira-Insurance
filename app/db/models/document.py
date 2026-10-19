"""Policy document and version ORM models."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BIGINT,
    DATE,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PolicyDocument(Base):
    """Logical document family (e.g., 'Health Guard Basic Policy Wording')."""

    __tablename__ = "policy_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_id: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    policy_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    plan_tier: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    versions: Mapped[list["PolicyDocumentVersion"]] = relationship(
        "PolicyDocumentVersion",
        back_populates="document",
        foreign_keys="PolicyDocumentVersion.document_id",
        lazy="select",
    )


class PolicyDocumentVersion(Base):
    """Immutable uploaded revision of a policy document."""

    __tablename__ = "policy_document_versions"
    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_docver_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("policy_documents.id"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BIGINT, nullable=False)
    effective_from: Mapped[date | None] = mapped_column(DATE, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(DATE, nullable=True)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="uploaded")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    qdrant_collection: Mapped[str] = mapped_column(String(128), nullable=False)
    ingestion_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    document: Mapped["PolicyDocument"] = relationship(
        "PolicyDocument",
        back_populates="versions",
        foreign_keys=[document_id],
    )
