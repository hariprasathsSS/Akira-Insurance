"""Unit tests for RAG components per Section 11 and 16."""
from __future__ import annotations

import os
import tempfile
import pytest

from app.rag.chunking import chunk_pages
from app.rag.pdf_extraction import PageChunk, extract_pages
from app.rag.qdrant_store import _sparse_vector
from app.rag.retrieval import format_citations
from scripts.generate_sample_pdfs import _build_minimal_pdf_bytes


def test_build_minimal_pdf_is_valid():
    """Verify that generated synthetic PDF has proper PDF header and trailer."""
    sections = [
        ("Section 1: General Coverage", "This is synthetic text for testing."),
        ("Section 2: Deductibles", "A deductible of 5000 applies."),
    ]
    pdf_bytes = _build_minimal_pdf_bytes("Health Test Policy", sections)
    assert pdf_bytes.startswith(b"%PDF-1.4")
    assert b"%%EOF" in pdf_bytes
    assert b"SYNTHETIC POC DOCUMENT" in pdf_bytes


def test_chunking_preserves_page_and_section():
    """Verify chunking maintains page numbers and detects section headers."""
    pages = [
        PageChunk(
            page_number=1,
            text=(
                "Section 1: Inpatient Hospitalization\n\n"
                "Coverage is provided for hospital room and boarding. " * 15
            ),
        ),
        PageChunk(
            page_number=2,
            text=(
                "Section 2: Exclusions\n\n"
                "Cosmetic and dental procedures are excluded. " * 10
            ),
        ),
    ]

    chunks = chunk_pages(pages)
    assert len(chunks) >= 2
    # Verify first chunk captured section and page
    assert chunks[0].page_number == 1
    assert "Section 1" in (chunks[0].section or "")

    # Verify second page captured page 2
    p2_chunks = [c for c in chunks if c.page_number == 2]
    assert len(p2_chunks) > 0
    assert "Section 2" in (p2_chunks[0].section or "")


def test_sparse_vector_generation():
    """Verify sparse vector produces indices and values from text."""
    text = "deductible coverage hospital accident"
    sparse = _sparse_vector(text)
    assert "indices" in sparse
    assert "values" in sparse
    assert len(sparse["indices"]) == 4
    assert len(sparse["values"]) == 4
    assert all(v >= 1.0 for v in sparse["values"])


def test_format_citations():
    """Verify format_citations maps hits cleanly to citation dictionaries."""
    hits = [
        {
            "chunk_id": "chk-123",
            "score": 0.88,
            "chunk_text": "Hospitalization room rent is capped at INR 5000 per day.",
            "page": 2,
            "section": "Section 1: Scope",
            "title": "Health Guard Policy",
        }
    ]
    citations = format_citations(hits)
    assert len(citations) == 1
    c = citations[0]
    assert c["chunk_id"] == "chk-123"
    assert c["score"] == 0.88
    assert c["page"] == 2
    assert c["section"] == "Section 1: Scope"
    assert "room rent" in c["excerpt"]
