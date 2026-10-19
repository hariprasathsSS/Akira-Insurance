"""Application-wide constants for AKIRA INSURANCE."""
from __future__ import annotations

# ─── Roles ────────────────────────────────────────────────────────────────────
ROLE_CUSTOMER = "customer"
ROLE_ADJUSTER = "adjuster"
ROLE_ADMIN = "admin"

ALL_ROLES = {ROLE_CUSTOMER, ROLE_ADJUSTER, ROLE_ADMIN}

# ─── Policy types ─────────────────────────────────────────────────────────────
POLICY_TYPE_HEALTH = "health"
POLICY_TYPE_MOTOR = "motor"
POLICY_TYPE_HOME = "home"

POLICY_TYPES = {POLICY_TYPE_HEALTH, POLICY_TYPE_MOTOR, POLICY_TYPE_HOME}

# ─── Policy statuses ─────────────────────────────────────────────────────────
POLICY_STATUS_ACTIVE = "active"
POLICY_STATUS_GRACE = "grace_period"
POLICY_STATUS_LAPSED = "lapsed"
POLICY_STATUS_CANCELLED = "cancelled"

# ─── Claim statuses ───────────────────────────────────────────────────────────
CLAIM_STATUS_DRAFT = "draft"
CLAIM_STATUS_SUBMITTED = "submitted"
CLAIM_STATUS_UNDER_REVIEW = "under_review"
CLAIM_STATUS_NEEDS_INFORMATION = "needs_information"
CLAIM_STATUS_EVALUATED = "evaluated"
CLAIM_STATUS_PENDING_APPROVAL = "pending_approval"
CLAIM_STATUS_APPROVED = "approved"
CLAIM_STATUS_DENIED = "denied"
CLAIM_STATUS_CLOSED = "closed"

# Valid state transitions: from → allowed next states
CLAIM_TRANSITIONS: dict[str, set[str]] = {
    CLAIM_STATUS_DRAFT: {CLAIM_STATUS_SUBMITTED},
    CLAIM_STATUS_SUBMITTED: {CLAIM_STATUS_UNDER_REVIEW, CLAIM_STATUS_NEEDS_INFORMATION},
    CLAIM_STATUS_UNDER_REVIEW: {
        CLAIM_STATUS_NEEDS_INFORMATION,
        CLAIM_STATUS_EVALUATED,
    },
    CLAIM_STATUS_NEEDS_INFORMATION: {CLAIM_STATUS_UNDER_REVIEW, CLAIM_STATUS_DENIED},
    CLAIM_STATUS_EVALUATED: {
        CLAIM_STATUS_PENDING_APPROVAL,
        CLAIM_STATUS_APPROVED,
        CLAIM_STATUS_DENIED,
    },
    CLAIM_STATUS_PENDING_APPROVAL: {CLAIM_STATUS_APPROVED, CLAIM_STATUS_DENIED},
    CLAIM_STATUS_APPROVED: {CLAIM_STATUS_CLOSED},
    CLAIM_STATUS_DENIED: {CLAIM_STATUS_CLOSED},
    CLAIM_STATUS_CLOSED: set(),
}

# ─── Decision types ───────────────────────────────────────────────────────────
DECISION_APPROVED = "approved"
DECISION_DENIED = "denied"
DECISION_REQUEST_INFORMATION = "request_information"
DECISION_AUTO_APPROVED = "auto_approved"

# ─── Document version statuses ────────────────────────────────────────────────
DOC_VERSION_UPLOADED = "uploaded"
DOC_VERSION_PROCESSING = "processing"
DOC_VERSION_INDEXED = "indexed"
DOC_VERSION_FAILED = "failed"
DOC_VERSION_SUPERSEDED = "superseded"
DOC_VERSION_ARCHIVED = "archived"

# ─── Job statuses ─────────────────────────────────────────────────────────────
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_SUCCEEDED = "succeeded"
JOB_STATUS_FAILED = "failed"

JOB_TYPE_POLICY_INGESTION = "policy_ingestion"

# ─── Validation flag codes ────────────────────────────────────────────────────
FLAG_FREQUENT_CLAIMS = "FREQUENT_CLAIMS_REVIEW"
FLAG_INCONSISTENT_DETAILS = "INCONSISTENT_INCIDENT_DETAILS"
FLAG_COVERAGE_UNCERTAIN = "COVERAGE_UNCERTAIN"
FLAG_POLICY_STATUS_REVIEW = "POLICY_STATUS_REVIEW"
FLAG_MISSING_FNOL_FIELDS = "MISSING_FNOL_FIELDS"
FLAG_AMOUNT_EXCEEDS_LIMIT = "AMOUNT_EXCEEDS_LIMIT"
FLAG_POLICY_VERSION_AMBIGUOUS = "POLICY_VERSION_AMBIGUOUS"

# ─── Chat intents ─────────────────────────────────────────────────────────────
INTENT_CHECK_PLAN_DETAILS = "CHECK_PLAN_DETAILS"
INTENT_CHECK_PAYMENT_STATUS = "CHECK_PAYMENT_STATUS"
INTENT_POLICY_RAG_QUERY = "POLICY_RAG_QUERY"
INTENT_LODGE_CLAIM_FNOL = "LODGE_CLAIM_FNOL"
INTENT_CHECK_CLAIM_STATUS = "CHECK_CLAIM_STATUS"
INTENT_UNKNOWN = "UNKNOWN"

VALID_INTENTS = {
    INTENT_CHECK_PLAN_DETAILS,
    INTENT_CHECK_PAYMENT_STATUS,
    INTENT_POLICY_RAG_QUERY,
    INTENT_LODGE_CLAIM_FNOL,
    INTENT_CHECK_CLAIM_STATUS,
    INTENT_UNKNOWN,
}

# ─── Currency ─────────────────────────────────────────────────────────────────
DEFAULT_CURRENCY = "INR"

# ─── Note types ───────────────────────────────────────────────────────────────
NOTE_TYPE_ADJUSTER = "adjuster"
NOTE_TYPE_CUSTOMER = "customer"
NOTE_TYPE_SYSTEM = "system"
