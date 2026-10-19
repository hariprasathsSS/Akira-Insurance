"""Intent classification for the customer chat agent."""
from __future__ import annotations

import logging
from typing import Optional

from app.core.constants import VALID_INTENTS, INTENT_UNKNOWN

logger = logging.getLogger(__name__)


def classify_intent_deterministic(message: str) -> Optional[str]:
    """
    Deterministic keyword-based intent classification.
    Used as primary when LLM is not configured, and as validation when LLM is used.
    """
    msg = message.lower()

    if any(kw in msg for kw in ["does my policy cover", "what does", "exclusion", "excluded", "covered", "wording", "clause"]):
        return "POLICY_RAG_QUERY"

    if any(kw in msg for kw in ["deductible", "plan details", "my plan", "my coverage", "sum insured", "idv"]):
        return "CHECK_PLAN_DETAILS"

    if any(kw in msg for kw in ["payment", "due", "bill", "premium", "paid"]):
        return "CHECK_PAYMENT_STATUS"

    if any(kw in msg for kw in ["claim status", "my claim", "claim id", "clm-"]):
        return "CHECK_CLAIM_STATUS"

    if any(kw in msg for kw in ["file a claim", "file claim", "lodge", "fnol", "report damage", "report accident"]):
        return "LODGE_CLAIM_FNOL"

    if "coverage" in msg or "plan" in msg:
        return "CHECK_PLAN_DETAILS"

    if "accident" in msg or "incident" in msg:
        return "LODGE_CLAIM_FNOL"

    return None


async def classify_intent_with_llm(message: str, llm) -> str:
    """Use LLM for intent classification, validated against allowed enum."""
    from app.llm.interfaces import LLMMessage
    system = (
        "You are an intent classifier for an insurance chatbot. "
        "Classify the user message into exactly one of these intents: "
        "CHECK_PLAN_DETAILS, CHECK_PAYMENT_STATUS, POLICY_RAG_QUERY, "
        "LODGE_CLAIM_FNOL, CHECK_CLAIM_STATUS, UNKNOWN. "
        "Respond with only the intent name, nothing else."
    )
    messages = [
        LLMMessage(role="system", content=system),
        LLMMessage(role="user", content=message[:500]),
    ]
    try:
        resp = await llm.complete(messages, temperature=0.0, max_tokens=20)
        intent = resp.content.strip().upper()
        if intent in VALID_INTENTS:
            return intent
        logger.warning(f"LLM returned unknown intent '{intent}', falling back.")
        return INTENT_UNKNOWN
    except Exception as exc:
        logger.warning(f"LLM intent classification failed: {exc}")
        return INTENT_UNKNOWN
