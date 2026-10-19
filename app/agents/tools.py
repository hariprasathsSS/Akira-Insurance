"""Typed tools for the LangGraph agent. Tools invoke services/repos; no raw SQL."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def fetch_user_policy_details(
    actor_id: str,
    session: AsyncSession,
    policy_public_id: Optional[str] = None,
) -> Dict[str, Any]:
    from app.db.repositories.policy_repository import PolicyRepository
    from app.db.repositories.user_repository import UserRepository
    repo = PolicyRepository(session)
    user_repo = UserRepository(session)
    import uuid
    user = await user_repo.get_by_id(uuid.UUID(actor_id))
    if not user:
        return {"error": "Actor not found."}
    if policy_public_id:
        policy = await repo.get_by_public_id(policy_public_id)
        if policy is None or policy.user_id != user.id:
            return {"error": "Policy not found."}
        return {
            "public_id": policy.public_id,
            "plan_name": policy.plan_name,
            "policy_type": policy.policy_type,
            "plan_tier": policy.plan_tier,
            "status": policy.status,
            "currency": policy.currency,
            "deductible": str(policy.deductible),
            "max_coverage": str(policy.max_coverage),
        }
    policies = await repo.get_by_user_id(user.id)
    return {
        "policies": [
            {
                "public_id": p.public_id,
                "plan_name": p.plan_name,
                "policy_type": p.policy_type,
                "status": p.status,
                "deductible": str(p.deductible),
                "max_coverage": str(p.max_coverage),
            }
            for p in policies
        ]
    }


async def check_billing_status(
    actor_id: str,
    session: AsyncSession,
    policy_public_id: Optional[str] = None,
) -> Dict[str, Any]:
    from app.db.repositories.billing_repository import BillingRepository
    from app.db.repositories.user_repository import UserRepository
    import uuid
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(uuid.UUID(actor_id))
    if not user:
        return {"error": "Actor not found."}
    repo = BillingRepository(session)
    records = await repo.get_by_user_id(user.id)
    return {
        "billing": [
            {
                "status": r.status,
                "amount_due": str(r.amount_due),
                "currency": r.currency,
            }
            for r in records
        ]
    }


async def fetch_claim_status(
    actor_id: str,
    session: AsyncSession,
    claim_public_id: Optional[str] = None,
) -> Dict[str, Any]:
    from app.db.repositories.claim_repository import ClaimRepository
    from app.db.repositories.user_repository import UserRepository
    import uuid
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(uuid.UUID(actor_id))
    if not user:
        return {"error": "Actor not found."}
    repo = ClaimRepository(session)
    if claim_public_id:
        claim = await repo.get_by_public_id(claim_public_id)
        if claim is None or claim.created_by_user_id != user.id:
            return {"error": "Claim not found."}
        return {
            "public_id": claim.public_id,
            "status": claim.status,
            "incident_type": claim.incident_type,
            "requested_amount": str(claim.requested_amount) if claim.requested_amount else None,
            "recommended_payout": str(claim.recommended_payout) if claim.recommended_payout else None,
        }
    claims = await repo.get_by_user_id(user.id, limit=5)
    return {
        "claims": [
            {"public_id": c.public_id, "status": c.status}
            for c in claims
        ]
    }


async def hybrid_search_qdrant_tool(
    query: str,
    policy_type: Optional[str] = None,
    plan_tier: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Wrapper for RAG retrieval — scope filters applied in Qdrant."""
    from app.rag.retrieval import retrieve_policy_chunks
    return retrieve_policy_chunks(
        query_text=query,
        policy_type=policy_type,
        plan_tier=plan_tier,
    )
