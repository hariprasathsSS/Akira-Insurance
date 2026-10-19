"""Customer LangGraph — handles plan details, billing, claims, and RAG queries."""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore
except ImportError:
    END = "__end__"
    START = "__start__"
    StateGraph = None

from app.agents.state import AgentState
from app.agents.intents import classify_intent_deterministic, classify_intent_with_llm
from app.agents.tools import (
    fetch_user_policy_details,
    check_billing_status,
    fetch_claim_status,
    hybrid_search_qdrant_tool,
)
from app.core.constants import (
    INTENT_CHECK_CLAIM_STATUS,
    INTENT_CHECK_PAYMENT_STATUS,
    INTENT_CHECK_PLAN_DETAILS,
    INTENT_LODGE_CLAIM_FNOL,
    INTENT_POLICY_RAG_QUERY,
    INTENT_UNKNOWN,
)
from app.core.exceptions import LLMNotConfigured
from app.observability.langfuse import start_trace

logger = logging.getLogger(__name__)


async def _classify(state: AgentState, **kwargs) -> AgentState:
    """Node: classify intent."""
    message = state["message"]
    # Try deterministic first
    intent = classify_intent_deterministic(message)
    if intent:
        return {**state, "intent": intent}

    # Try LLM if available
    try:
        from app.llm.factory import get_llm_provider
        llm = get_llm_provider()
        intent = await classify_intent_with_llm(message, llm)
    except LLMNotConfigured:
        intent = INTENT_UNKNOWN
    return {**state, "intent": intent}


async def _handle_plan_details(state: AgentState, session, **kwargs) -> AgentState:
    result = await fetch_user_policy_details(
        actor_id=state["actor_id"],
        session=session,
        policy_public_id=state.get("policy_public_id"),
    )
    answer = _format_policy_answer(result, state["message"])
    return {**state, "tool_results": result, "response": answer}


async def _handle_billing(state: AgentState, session, **kwargs) -> AgentState:
    result = await check_billing_status(
        actor_id=state["actor_id"],
        session=session,
    )
    billing = result.get("billing", [])
    if billing:
        lines = [f"Status: {b['status']}, Amount Due: {b['currency']} {b['amount_due']}" for b in billing]
        answer = "Your billing summary:\n" + "\n".join(lines)
    else:
        answer = "No billing records found."
    return {**state, "tool_results": result, "response": answer}


async def _handle_claim_status(state: AgentState, session, **kwargs) -> AgentState:
    result = await fetch_claim_status(
        actor_id=state["actor_id"],
        session=session,
        claim_public_id=state.get("claim_public_id"),
    )
    if "error" in result:
        answer = result["error"]
    elif "claims" in result:
        claims = result["claims"]
        if claims:
            lines = [f"Claim {c['public_id']}: {c['status']}" for c in claims]
            answer = "Your recent claims:\n" + "\n".join(lines)
        else:
            answer = "You have no claims on record."
    else:
        answer = f"Claim {result.get('public_id')}: Status is {result.get('status')}."
    return {**state, "tool_results": result, "response": answer}


async def _handle_rag_query(state: AgentState, session, **kwargs) -> AgentState:
    # Determine policy scope from actor's policies
    from app.db.repositories.policy_repository import PolicyRepository
    from app.db.repositories.user_repository import UserRepository
    import uuid as _uuid
    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(_uuid.UUID(state["actor_id"]))
    policy_type = None
    plan_tier = None
    if user:
        policy_repo = PolicyRepository(session)
        policies = await policy_repo.get_by_user_id(user.id)
        if policies:
            policy_type = policies[0].policy_type
            plan_tier = policies[0].plan_tier

    hits = await hybrid_search_qdrant_tool(
        query=state["message"],
        policy_type=policy_type,
        plan_tier=plan_tier,
    )

    if not hits:
        answer = (
            "I couldn't find specific policy wording for your query. "
            "Please contact our support team or refer to your policy document."
        )
        citations = []
    else:
        context = "\n\n".join(h["chunk_text"][:400] for h in hits[:3])
        # Generate answer using LLM if available
        try:
            from app.llm.factory import get_llm_provider
            from app.llm.interfaces import LLMMessage
            llm = get_llm_provider()
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "You are an insurance assistant. Answer the user's question using ONLY "
                        "the provided policy context below. Do not invent coverage terms. "
                        "If the context doesn't answer the question, say so clearly.\n\n"
                        f"Policy context:\n{context}"
                    ),
                ),
                LLMMessage(role="user", content=state["message"]),
            ]
            resp = await llm.complete(messages, temperature=0.1, max_tokens=500)
            answer = resp.content
        except LLMNotConfigured:
            answer = f"Based on policy documents:\n\n{context[:600]}"

        from app.rag.retrieval import format_citations
        citations = format_citations(hits)

    return {**state, "retrieved_evidence": hits, "citations": citations, "response": answer}


async def _handle_fnol(state: AgentState, **kwargs) -> AgentState:
    answer = (
        "To file a claim, please use the POST /api/v1/claims endpoint with your policy ID, "
        "incident details, and a unique idempotency key. "
        "Required fields: policy_public_id, incident_type, incident_date, "
        "incident_description, requested_amount."
    )
    return {
        **state,
        "response": answer,
        "needs_clarification": True,
        "actions": [
            {"action_type": "navigate", "label": "File Claim", "params": {"endpoint": "POST /api/v1/claims"}}
        ],
    }


async def _handle_unknown(state: AgentState, **kwargs) -> AgentState:
    return {
        **state,
        "response": (
            "I'm sorry, I didn't understand your request. "
            "You can ask me about your plan details, payment status, claim status, "
            "or policy coverage questions."
        ),
        "needs_clarification": True,
    }


def _format_policy_answer(result: Dict[str, Any], message: str) -> str:
    if "error" in result:
        return result["error"]
    if "policies" in result:
        items = result["policies"]
        if not items:
            return "No policies found on your account."
        lines = [
            f"- {p['plan_name']} ({p['policy_type']}): Status {p['status']}, "
            f"Coverage ₹{p['max_coverage']}, Deductible ₹{p['deductible']}"
            for p in items
        ]
        return "Your policies:\n" + "\n".join(lines)
    return (
        f"Policy {result.get('public_id')}: {result.get('plan_name')} — "
        f"Status: {result.get('status')}, "
        f"Coverage: ₹{result.get('max_coverage')}, "
        f"Deductible: ₹{result.get('deductible')}."
    )


def _route_intent(state: AgentState) -> str:
    intent = state.get("intent") or INTENT_UNKNOWN
    mapping = {
        INTENT_CHECK_PLAN_DETAILS: "handle_plan",
        INTENT_CHECK_PAYMENT_STATUS: "handle_billing",
        INTENT_CHECK_CLAIM_STATUS: "handle_claim",
        INTENT_POLICY_RAG_QUERY: "handle_rag",
        INTENT_LODGE_CLAIM_FNOL: "handle_fnol",
        INTENT_UNKNOWN: "handle_unknown",
    }
    return mapping.get(intent, "handle_unknown")


async def run_customer_graph(state: AgentState, session) -> AgentState:
    """Run the customer support LangGraph. Returns updated state."""
    trace = start_trace(
        name="customer_chat",
        user_id=state["actor_public_id"],
        metadata={"intent": state.get("intent"), "request_id": state["request_id"]},
    )

    # Step 1: classify
    state = await _classify(state)

    # Step 2: route
    route = _route_intent(state)

    # Step 3: handle
    handlers = {
        "handle_plan": _handle_plan_details,
        "handle_billing": _handle_billing,
        "handle_claim": _handle_claim_status,
        "handle_rag": _handle_rag_query,
        "handle_fnol": _handle_fnol,
        "handle_unknown": _handle_unknown,
    }
    handler = handlers.get(route, _handle_unknown)
    state = await handler(state, session=session)

    try:
        trace.update(output=state.get("response", "")[:200])
        trace.end()
    except Exception:
        pass

    return state
