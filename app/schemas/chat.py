"""Chat Pydantic schemas."""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatContext(BaseModel):
    claim_public_id: Optional[str] = None
    policy_public_id: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    conversation_id: Optional[uuid.UUID] = None
    context: ChatContext = Field(default_factory=ChatContext)


class CitationResponse(BaseModel):
    chunk_id: str
    document_title: str
    section: Optional[str] = None
    page: Optional[int] = None
    excerpt: str
    score: float


class SuggestedAction(BaseModel):
    action_type: str
    label: str
    params: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    intent: str
    answer: str
    data: Optional[Dict[str, Any]] = None
    citations: List[CitationResponse] = []
    actions: List[SuggestedAction] = []
    trace_id: Optional[str] = None
    needs_clarification: bool = False
