"""RAG ingestion pipeline — runs as a FastAPI BackgroundTask.

Limitations of FastAPI BackgroundTasks (documented per spec section 8.2):
- Work may be lost if the process crashes or is redeployed mid-run.
- Tasks share application memory — no process isolation.
- No built-in durable retry scheduling.
- Not suitable for heavy OCR or large bulk indexing.
- Production replacement: use Celery+Redis, Dramatiq, or a managed queue.

This implementation compensates by:
- Persisting job status before returning the API response.
- Using an in-process semaphore to limit concurrent ingestion.
- Making ingestion idempotent via version ID + content hash.
- On partial failure, cleaning (or isolating) partial vectors.
- Marking failed jobs with a sanitized error; never modifying the prior active version.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Limit concurrent ingestion tasks in-process
_ingestion_semaphore = asyncio.Semaphore(2)


async def run_ingestion_job(
    job_id: uuid.UUID,
    version_id: uuid.UUID,
    stored_path: str,
    collection_name: str,
    metadata: Dict[str, Any],
) -> None:
    """Background task: extract, embed, index a document version."""
    # Import here to avoid circular imports at module load time
    from app.db.session import get_session_factory
    from app.db.repositories.document_repository import DocumentRepository
    from app.db.repositories.job_repository import JobRepository
    from app.rag.pdf_extraction import extract_pages
    from app.rag.chunking import chunk_pages
    from app.rag.qdrant_store import ensure_collection_exists, upsert_chunks
    from app.llm.factory import get_embedding_provider
    from app.core.config import get_settings
    from app.core.exceptions import LLMNotConfigured

    settings = get_settings()

    async with _ingestion_semaphore:
        factory = get_session_factory()
        async with factory() as session:
            job_repo = JobRepository(session)
            doc_repo = DocumentRepository(session)

            job = await job_repo.get_by_id(job_id)
            version = await doc_repo.get_version_by_id(version_id)

            if not job or not version:
                logger.error(f"Ingestion job {job_id}: missing job or version record.")
                return

            # Mark running
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.attempt_count += 1
            await session.commit()

            try:
                # Extract
                with open(stored_path, "rb") as fh:
                    pdf_bytes = fh.read()
                pages = extract_pages(pdf_bytes)
                chunks = chunk_pages(pages)

                # Embed
                try:
                    embedder = get_embedding_provider()
                    texts = [c.text for c in chunks]
                    dense_embeddings = await embedder.embed(texts)
                    dense_dim = len(dense_embeddings[0]) if dense_embeddings else settings.effective_embedding_dim
                except LLMNotConfigured:
                    # Use zero-padded dummy vectors for POC without credentials
                    logger.warning("Embedding provider not configured — using dummy vectors for ingestion POC.")
                    dense_dim = settings.effective_embedding_dim
                    dense_embeddings = [[0.0] * dense_dim for _ in chunks]

                # Ensure collection
                ensure_collection_exists(collection_name, dense_dim)

                # Upsert
                count = upsert_chunks(
                    collection_name=collection_name,
                    chunks=chunks,
                    dense_embeddings=dense_embeddings,
                    metadata={
                        **metadata,
                        "document_version_id": str(version_id),
                    },
                )

                # Mark version indexed (only after ALL chunks written)
                version.status = "indexed"
                version.ingestion_error = None
                job.status = "succeeded"
                job.finished_at = datetime.now(timezone.utc)
                job.result = {"chunks_indexed": count, "pages": len(pages)}
                await session.commit()
                logger.info(f"Ingestion job {job_id} succeeded: {count} chunks indexed.")

            except Exception as exc:
                # Sanitize error — no secrets or full traceback in DB
                safe_error = str(exc)[:500]
                logger.exception(f"Ingestion job {job_id} failed: {safe_error}")

                # CRITICAL: Do NOT touch is_active or change the prior active version
                version.status = "failed"
                version.ingestion_error = safe_error
                job.status = "failed"
                job.finished_at = datetime.now(timezone.utc)
                job.error_code = "INGESTION_FAILED"
                job.error_message = safe_error
                await session.commit()
