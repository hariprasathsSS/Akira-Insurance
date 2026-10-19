"""Qdrant hybrid dense+sparse vector store.

Dense vectors from configured embedding provider.
Sparse vectors use a simple TF-IDF-style tokenizer (POC — compatible with Qdrant's
sparse vector search). For production, integrate a proper BM25 encoder.

POC note: Sparse vectors here use a simple token-frequency approach. In production,
use a proper BM25 encoder (e.g. qdrant/fastembed BM25 or beir/bm25).
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.core.exceptions import RAGNotReady

logger = logging.getLogger(__name__)


def _get_client():
    settings = get_settings()
    try:
        from qdrant_client import QdrantClient  # type: ignore
        kwargs: Dict[str, Any] = {"url": settings.QDRANT_URL}
        if settings.QDRANT_API_KEY:
            kwargs["api_key"] = settings.QDRANT_API_KEY
        return QdrantClient(**kwargs)
    except Exception as exc:
        raise RAGNotReady(f"Cannot connect to Qdrant: {exc}")


def _sparse_vector(text: str) -> Dict[str, Any]:
    """Simple token frequency sparse vector for POC hybrid search."""
    import re
    tokens = re.findall(r'\b[a-zA-Z0-9]+\b', text.lower())
    freq: Dict[str, int] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    # Use hash of token as index (bounded to 2^16)
    indices = []
    values = []
    for token, count in freq.items():
        indices.append(abs(hash(token)) % 65536)
        values.append(float(count))
    return {"indices": indices, "values": values}


def ensure_collection_exists(collection_name: str, dense_dim: int) -> None:
    """Create Qdrant collection with dense and sparse vectors if missing."""
    try:
        client = _get_client()
        from qdrant_client.models import (  # type: ignore
            Distance,
            VectorParams,
            SparseVectorParams,
            SparseIndexParams,
        )
        existing = [c.name for c in client.get_collections().collections]
        if collection_name not in existing:
            client.create_collection(
                collection_name=collection_name,
                vectors_config={"dense": VectorParams(size=dense_dim, distance=Distance.COSINE)},
                sparse_vectors_config={
                    "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
                },
            )
            logger.info(f"Created Qdrant collection '{collection_name}'.")
    except Exception as exc:
        logger.warning(f"Could not ensure Qdrant collection: {exc}")


def upsert_chunks(
    collection_name: str,
    chunks: list,
    dense_embeddings: List[List[float]],
    metadata: Dict[str, Any],
) -> int:
    """Upsert chunk points with dense and sparse vectors."""
    from qdrant_client.models import PointStruct, SparseVector  # type: ignore
    client = _get_client()
    points = []
    for chunk, dense_vec in zip(chunks, dense_embeddings):
        sparse = _sparse_vector(chunk.text)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{metadata['document_version_id']}:{chunk.chunk_index}"))
        payload = {
            **metadata,
            "chunk_index": chunk.chunk_index,
            "page": chunk.page,
            "section": chunk.section,
            "chunk_text": chunk.text,
        }
        points.append(
            PointStruct(
                id=point_id,
                vector={
                    "dense": dense_vec,
                    "sparse": SparseVector(indices=sparse["indices"], values=sparse["values"]),
                },
                payload=payload,
            )
        )
    if points:
        client.upsert(collection_name=collection_name, points=points)
    return len(points)


def hybrid_search(
    collection_name: str,
    query_text: str,
    dense_vector: List[float],
    top_k: int = 8,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Hybrid dense+sparse search with RRF fusion."""
    try:
        from qdrant_client.models import (  # type: ignore
            Filter,
            FieldCondition,
            MatchValue,
            NamedVector,
            NamedSparseVector,
            SparseVector,
            SearchRequest,
            Prefetch,
            FusionQuery,
            Fusion,
        )
        client = _get_client()
        sparse = _sparse_vector(query_text)

        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            if conditions:
                qdrant_filter = Filter(must=conditions)

        results = client.query_points(
            collection_name=collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=top_k * 2,
                    filter=qdrant_filter,
                ),
                Prefetch(
                    query=SparseVector(indices=sparse["indices"], values=sparse["values"]),
                    using="sparse",
                    limit=top_k * 2,
                    filter=qdrant_filter,
                ),
            ],
            query=FusionQuery(fusion=Fusion.RRF),
            limit=top_k,
            with_payload=True,
        )

        hits = []
        for r in results.points:
            payload = r.payload or {}
            hits.append({
                "chunk_id": str(r.id),
                "score": r.score,
                "chunk_text": payload.get("chunk_text", ""),
                "page": payload.get("page"),
                "section": payload.get("section"),
                "document_id": payload.get("document_id"),
                "document_version_id": payload.get("document_version_id"),
                "version_number": payload.get("version_number"),
                "policy_type": payload.get("policy_type"),
                "plan_tier": payload.get("plan_tier"),
            })
        return hits
    except Exception as exc:
        logger.warning(f"Qdrant hybrid search failed: {exc}")
        return []


def check_qdrant_health() -> bool:
    try:
        client = _get_client()
        client.get_collections()
        return True
    except Exception:
        return False
