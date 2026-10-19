"""Text chunking — section-aware splitting with page metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.rag.pdf_extraction import PageChunk

CHUNK_SIZE = 800  # characters per chunk
OVERLAP = 100


@dataclass
class TextChunk:
    chunk_index: int
    page: int
    section: str
    text: str
    char_count: int

    @property
    def page_number(self) -> int:
        return self.page


def chunk_pages(
    pages: List[PageChunk],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> List[TextChunk]:
    """Split page text into overlapping chunks, preserving page numbers."""
    from app.core.config import get_settings

    settings = get_settings()
    actual_chunk_size = chunk_size if chunk_size is not None else settings.CHUNK_SIZE
    actual_overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP_SIZE
    chunks = []
    idx = 0
    for page in pages:
        text = page.text
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(start + actual_chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    TextChunk(
                        chunk_index=idx,
                        page=page.page,
                        section=_detect_section(chunk_text),
                        text=chunk_text,
                        char_count=len(chunk_text),
                    )
                )
                idx += 1
            start = end - actual_overlap if end < len(text) else len(text)
    return chunks


def _detect_section(text: str) -> str:
    """Heuristic: use first line as section label if it looks like a heading."""
    first_line = text.split("\n")[0].strip()
    if first_line and len(first_line) < 80 and first_line.isupper():
        return first_line
    if first_line and len(first_line) < 80 and first_line[0].isupper():
        return first_line
    return "content"
