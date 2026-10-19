"""LangGraph agent state definition."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class AgentState(TypedDict):
    request_id: str
    actor_id: str  # UUID str
    actor_public_id: str
    actor_role: str
    message: str
    conversation_id: str
    intent: Optional[str]
    policy_public_id: Optional[str]
    claim_public_id: Optional[str]
    tool_results: Dict[str, Any]
    retrieved_evidence: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    structured_facts: Dict[str, Any]
    validation_flags: List[Dict[str, Any]]
    calculation_breakdown: Dict[str, Any]
    recommended_payout: Optional[str]
    requires_human_review: bool
    response: str
    error_code: Optional[str]
    trace_id: str
    needs_clarification: bool
