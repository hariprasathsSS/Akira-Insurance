"""Model registry — import all models so Alembic autogenerate detects them."""
from app.db.models.user import User
from app.db.models.policy import Policy
from app.db.models.billing import BillingRecord
from app.db.models.claim import Claim, ClaimNote, ClaimEvaluation, ClaimDecision, ClaimEvent
from app.db.models.document import PolicyDocument, PolicyDocumentVersion
from app.db.models.job import BackgroundJob
from app.db.models.audit import AuditLog

__all__ = [
    "User",
    "Policy",
    "BillingRecord",
    "Claim",
    "ClaimNote",
    "ClaimEvaluation",
    "ClaimDecision",
    "ClaimEvent",
    "PolicyDocument",
    "PolicyDocumentVersion",
    "BackgroundJob",
    "AuditLog",
]
