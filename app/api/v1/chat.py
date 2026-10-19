"""Chat endpoint per Section 7.3 and 9."""
from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.customer_graph import run_customer_graph
from app.agents.state import AgentState
from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.exceptions import LLMNotConfigured
from app.db.models.user import User
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    CitationResponse,
    SuggestedAction,
)

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Chat with the customer support AI assistant.
    
    Supported intents:
    - CHECK_PLAN_DETAILS: Structured lookups against the user's active policies.
    - CHECK_PAYMENT_STATUS: Structured billing queries.
    - CHECK_CLAIM_STATUS: Status of recent or specific claims.
    - POLICY_RAG_QUERY: Hybrid dense+sparse retrieval over ingested policy documents.
    - LODGE_CLAIM_FNOL: Guidance and required parameters for claim lodging.
    - UNKNOWN: Safe fallback requesting clarification.
    """
    settings = get_settings()

    # Enforce configured max chat message length
    if len(req.message) > settings.MAX_CHAT_MESSAGE_CHARS:
        from app.core.exceptions import ValidationError
        raise ValidationError(
            f"Message exceeds maximum length of {settings.MAX_CHAT_MESSAGE_CHARS} characters."
        )

    conv_id = req.conversation_id or uuid.uuid4()
    req_id = str(uuid.uuid4())

    state: AgentState = {
        "conversation_id": str(conv_id),
        "request_id": req_id,
        "actor_id": str(user.id),
        "actor_public_id": user.public_id,
        "message": req.message,
        "claim_public_id": req.context.claim_public_id if req.context else None,
        "policy_public_id": req.context.policy_public_id if req.context else None,
        "intent": None,
        "tool_results": {},
        "retrieved_evidence": [],
        "citations": [],
        "response": "",
        "needs_clarification": False,
        "actions": [],
    }

    result_state = await run_customer_graph(state, session=session)

    citations = [
        CitationResponse(
            chunk_id=c.get("chunk_id", ""),
            document_title=c.get("document_title", "Policy Document"),
            section=c.get("section"),
            page=c.get("page"),
            excerpt=c.get("excerpt", ""),
            score=float(c.get("score", 0.0)),
        )
        for c in result_state.get("citations", [])
    ]

    actions = [
        SuggestedAction(
            action_type=a.get("action_type", ""),
            label=a.get("label", ""),
            params=a.get("params", {}),
        )
        for a in result_state.get("actions", [])
    ]

    return ChatResponse(
        conversation_id=conv_id,
        intent=result_state.get("intent") or "UNKNOWN",
        answer=result_state.get("response", ""),
        data=result_state.get("tool_results") or None,
        citations=citations,
        actions=actions,
        trace_id=req_id,
        needs_clarification=result_state.get("needs_clarification", False),
    )
