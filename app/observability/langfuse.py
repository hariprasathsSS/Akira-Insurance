"""Langfuse observability — tracing for model calls, graph runs, tools, retrieval.

If Langfuse is unavailable or unconfigured, the application continues working;
a warning is logged but requests are not rejected.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def _get_langfuse():
    global _client, _initialized
    if _initialized:
        return _client
    _initialized = True
    settings = get_settings()
    if not settings.langfuse_configured:
        logger.warning(
            "Langfuse not configured (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY missing). "
            "Observability traces will be skipped."
        )
        return None
    try:
        from langfuse import Langfuse  # type: ignore
        _client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_HOST,
        )
        logger.info("Langfuse client initialized.", extra={"host": settings.LANGFUSE_HOST})
    except Exception as exc:
        logger.warning(f"Failed to initialize Langfuse client: {exc}. Tracing disabled.")
    return _client


class _NoopSpan:
    """Null object — no-op span when Langfuse is unavailable."""
    def end(self, **kwargs): pass
    def update(self, **kwargs): pass


class _NoopTrace:
    """Null object — no-op trace."""
    @property
    def id(self): return "no-trace"
    def span(self, **kwargs): return _NoopSpan()
    def generation(self, **kwargs): return _NoopSpan()
    def end(self, **kwargs): pass
    def update(self, **kwargs): pass


def start_trace(
    name: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    client = _get_langfuse()
    if client is None:
        return _NoopTrace()
    try:
        trace = client.trace(
            name=name,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {},
        )
        return trace
    except Exception as exc:
        logger.debug(f"Langfuse trace creation failed: {exc}")
        return _NoopTrace()


def flush():
    client = _get_langfuse()
    if client is not None:
        try:
            client.flush()
        except Exception:
            pass
