"""RAG retrieval — hybrid search with scope filters and citations."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import LLMNotConfigured, RAGNotReady
from app.rag.qdrant_store import hybrid_search

logger = logging.getLogger(__name__)


def retrieve_policy_chunks(
    query_text: str,
    policy_type: Optional[str] = None,
    plan_tier: Optional[str] = None,
    top_k: Optional[int] = None,
    min_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Retrieve chunks scoped to policy_type/plan_tier. Filters applied in Qdrant, not by model."""
    settings = get_settings()
    k = top_k or settings.RAG_TOP_K
    min_s = min_score if min_score is not None else settings.RAG_MIN_SCORE

    # Build scope filters
    qdrant_filter: Dict[str, Any] = {}
    if policy_type:
        qdrant_filter["policy_type"] = policy_type
    if plan_tier:
        qdrant_filter["plan_tier"] = plan_tier

    # Get dense embedding
    try:
        from app.llm.factory import get_embedding_provider
        embedder = get_embedding_provider()
        # Run synchronously in this context (retrieval called from async via asyncio.run or await)
        import asyncio

        async def _embed():
            return await embedder.embed([query_text])

        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _embed())
                embeddings = future.result()
        else:
            embeddings = loop.run_until_complete(_embed())

        dense_vector = embeddings[0]
    except LLMNotConfigured:
        logger.warning("Embedding not configured — using zero vector for RAG (POC mode).")
        dense_vector = [0.0] * settings.effective_embedding_dim

    hits = hybrid_search(
        collection_name=settings.QDRANT_COLLECTION,
        query_text=query_text,
        dense_vector=dense_vector,
        top_k=k,
        filters=qdrant_filter if qdrant_filter else None,
    )

    # Normalize RRF scores (Qdrant reciprocal rank fusion scores are <= ~0.033)
    for h in hits:
        s = h.get("score", 0.0)
        if 0 < s < 0.1:
            h["score"] = min(1.0, s / 0.033)

    # Apply minimum score filter
    if min_s:
        hits = [h for h in hits if h.get("score", 0) >= min_s]

    return hits


def format_citations(hits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format hits into citation objects safe to return in API responses."""
    return [
        {
            "chunk_id": h["chunk_id"],
            "document_title": h.get("document_title") or h.get("plan_tier", "Policy Document"),
            "section": h.get("section"),
            "page": h.get("page"),
            "excerpt": h["chunk_text"][:300],
            "score": round(h.get("score", 0.0), 4),
        }
        for h in hits
    ]
