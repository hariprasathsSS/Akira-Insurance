"""PDF extraction — page boundaries and section metadata."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.core.exceptions import DocumentInvalid


@dataclass
class PageChunk:
    page: int = 1
    text: str = ""
    char_count: int = 0
    page_number: int = 1

    def __post_init__(self):
        if self.page_number != 1 and self.page == 1:
            self.page = self.page_number
        elif self.page != 1 and self.page_number == 1:
            self.page_number = self.page
        if not self.char_count and self.text:
            self.char_count = len(self.text)


def extract_pages(pdf_bytes: bytes) -> List[PageChunk]:
    """Extract text per page from a PDF. Raises DocumentInvalid for malformed files."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise DocumentInvalid("PDF extraction library (PyMuPDF) is not installed.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise DocumentInvalid(f"Failed to open PDF: {exc}")

    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        pages.append(PageChunk(page=page_num + 1, text=text, char_count=len(text)))

    doc.close()

    if not any(p.char_count > 0 for p in pages):
        raise DocumentInvalid("PDF appears to have no extractable text content.")

    return pages
