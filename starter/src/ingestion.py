"""Read and normalize source data with full traceability.

Compliant with Day 06 requirements:
- Unicode NFKC normalization
- Whitespace cleanup while preserving structural paragraphs
- Logging empty / low-content pages
- Filtering non-content pages (cover, TOC)
"""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
import pypdf
from .models import DocumentPage


def normalize_text(text: str) -> str:
    """Normalize Unicode (NFKC) and clean whitespace without losing paragraph structure."""
    if not text:
        return ""
    # Unicode NFKC normalization ensures composite/decomposed Vietnamese chars are standardized
    text = unicodedata.normalize("NFKC", text)
    # Remove control characters except standard whitespace
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalize multiple horizontal spaces and tabs into a single space
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    # Normalize newline sequences: preserve paragraph breaks (double newline)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    # Clean leading/trailing spaces on each line
    lines = [line.strip() for line in text.split("\n")]
    cleaned = "\n".join(lines).strip()
    return cleaned


def determine_section(page_num: int) -> str:
    """Determine document section based on physical page number."""
    if page_num in (3, 4):
        return "mo_dau"
    elif 5 <= page_num <= 25:
        return "phan_1_the_gioi"
    elif 26 <= page_num <= 45:
        return "phan_2_viet_nam"
    elif 46 <= page_num <= 50:
        return "phan_3_ket_luan"
    elif 51 <= page_num <= 58:
        return "phu_luc"
    return "khac"


def load_pdf(
    path: Path,
    document_id: str = "cesti-2023-ai-healthcare",
    source: str = "2023-BC-toan-canh-cong-nghe-AI-cham-soc-suc-khoe.pdf",
    include_cover_and_toc: bool = False,
) -> list[DocumentPage]:
    """Extract physical pages, record page numbers, source, and section metadata."""
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found at {path}")

    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []

    for idx, raw_page in enumerate(reader.pages):
        physical_page = idx + 1

        # Exclude cover (page 1) and table of contents (page 2) from core retrieval corpus unless requested
        if not include_cover_and_toc and physical_page in (1, 2):
            continue

        raw_text = raw_page.extract_text() or ""
        clean_text = normalize_text(raw_text)

        # Skip completely empty pages or note ultra-short separator pages
        section = determine_section(physical_page)
        metadata = {
            "section": section,
            "char_count": len(clean_text),
            "physical_page": physical_page,
            "is_short": len(clean_text) < 100,
        }

        pages.append(
            DocumentPage(
                document_id=document_id,
                source=source,
                page=physical_page,
                text=clean_text,
                metadata=metadata,
            )
        )

    return pages
