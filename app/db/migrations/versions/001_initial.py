"""Initial schema — all tables for AKIRA INSURANCE.

Revision ID: 001_initial
Revises: 
Create Date: 2026-10-19

"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("role", sa.String(24), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_public_id", "users", ["public_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ── policy_documents ────────────────────────────────────────────────────
    op.create_table(
        "policy_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_id", sa.String(80), nullable=False),
        sa.Column("policy_type", sa.String(24), nullable=False),
        sa.Column("plan_tier", sa.String(80), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_policy_documents_public_id", "policy_documents", ["public_id"], unique=True)
    op.create_index("ix_policy_documents_policy_type", "policy_documents", ["policy_type"])
    op.create_index("ix_policy_documents_plan_tier", "policy_documents", ["plan_tier"])

    # ── policy_document_versions ─────────────────────────────────────────────
    op.create_table(
        "policy_document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("policy_documents.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_path", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False, server_default="uploaded"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("qdrant_collection", sa.String(128), nullable=False),
        sa.Column("ingestion_error", sa.Text(), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("document_id", "version_number", name="uq_docver_number"),
    )
    op.create_index("ix_policy_document_versions_document_id", "policy_document_versions", ["document_id"])
    op.create_index("ix_policy_document_versions_is_active", "policy_document_versions", ["is_active"])

    # ── policies ─────────────────────────────────────────────────────────────
    op.create_table(
        "policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("plan_name", sa.String(160), nullable=False),
        sa.Column("policy_type", sa.String(24), nullable=False),
        sa.Column("plan_tier", sa.String(80), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="INR"),
        sa.Column("deductible", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("max_coverage", sa.Numeric(14, 2), nullable=False),
        sa.Column("policy_number", sa.String(80), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column(
            "current_document_version_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("policy_document_versions.id", name="fk_policy_current_docver", use_alter=True),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_policies_public_id", "policies", ["public_id"], unique=True)
    op.create_index("ix_policies_user_id", "policies", ["user_id"])
    op.create_index("ix_policies_policy_type", "policies", ["policy_type"])
    op.create_index("ix_policies_status", "policies", ["status"])
    op.create_index("ix_policies_policy_number", "policies", ["policy_number"], unique=True)

    # ── billing_records ───────────────────────────────────────────────────────
    op.create_table(
        "billing_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("premium_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("amount_due", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("last_paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reference", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_billing_records_policy_id", "billing_records", ["policy_id"])

    # ── claims ────────────────────────────────────────────────────────────────
    op.create_table(
        "claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="draft"),
        sa.Column("incident_type", sa.String(80), nullable=True),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("incident_location", sa.String(255), nullable=True),
        sa.Column("incident_description", sa.Text(), nullable=True),
        sa.Column("requested_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("adjuster_notes_latest", sa.Text(), nullable=True),
        sa.Column("recommended_payout", sa.Numeric(12, 2), nullable=True),
        sa.Column("approved_payout", sa.Numeric(12, 2), nullable=True),
        sa.Column("fraud_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("idempotency_key", sa.String(255), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_claims_public_id", "claims", ["public_id"], unique=True)
    op.create_index("ix_claims_policy_id", "claims", ["policy_id"])
    op.create_index("ix_claims_status", "claims", ["status"])
    op.create_index("ix_claims_idempotency_key", "claims", ["idempotency_key"])

    # ── claim_notes ───────────────────────────────────────────────────────────
    op.create_table(
        "claim_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("author_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("note_type", sa.String(24), nullable=False, server_default="system"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_claim_notes_claim_id", "claim_notes", ["claim_id"])

    # ── claim_evaluations ─────────────────────────────────────────────────────
    op.create_table(
        "claim_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("model_provider", sa.String(80), nullable=True),
        sa.Column("model_name", sa.String(120), nullable=True),
        sa.Column("extracted_facts", postgresql.JSONB(), nullable=True),
        sa.Column("validation_flags", postgresql.JSONB(), nullable=True),
        sa.Column("coverage_findings", postgresql.JSONB(), nullable=True),
        sa.Column("estimate_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("deductible_applied", sa.Numeric(12, 2), nullable=True),
        sa.Column("limit_applied", sa.Numeric(12, 2), nullable=True),
        sa.Column("recommended_payout", sa.Numeric(12, 2), nullable=True),
        sa.Column("calculation_breakdown", postgresql.JSONB(), nullable=True),
        sa.Column("requires_human_review", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("evaluation_status", sa.String(24), nullable=False),
        sa.Column("trace_id", sa.String(128), nullable=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("claim_id", "version", name="uq_claim_evaluation_version"),
    )
    op.create_index("ix_claim_evaluations_claim_id", "claim_evaluations", ["claim_id"])

    # ── claim_decisions ───────────────────────────────────────────────────────
    op.create_table(
        "claim_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claim_evaluations.id"), nullable=True),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("decided_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("approved_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_automated", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_claim_decisions_claim_id", "claim_decisions", ["claim_id"])

    # ── claim_events ──────────────────────────────────────────────────────────
    op.create_table(
        "claim_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("claim_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("claims.id"), nullable=False),
        sa.Column("from_status", sa.String(32), nullable=True),
        sa.Column("to_status", sa.String(32), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_claim_events_claim_id", "claim_events", ["claim_id"])

    # ── background_jobs ───────────────────────────────────────────────────────
    op.create_table(
        "background_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("public_id", sa.String(80), nullable=False),
        sa.Column("job_type", sa.String(40), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("requested_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_background_jobs_public_id", "background_jobs", ["public_id"], unique=True)
    op.create_index("ix_background_jobs_status", "background_jobs", ["status"])
    op.create_index("ix_background_jobs_job_type", "background_jobs", ["job_type"])

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(80), nullable=False),
        sa.Column("resource_id", sa.String(100), nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("outcome", sa.String(24), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("background_jobs")
    op.drop_table("claim_events")
    op.drop_table("claim_decisions")
    op.drop_table("claim_evaluations")
    op.drop_table("claim_notes")
    op.drop_table("claims")
    op.drop_table("billing_records")
    op.drop_table("policies")
    op.drop_table("policy_document_versions")
    op.drop_table("policy_documents")
    op.drop_table("users")
