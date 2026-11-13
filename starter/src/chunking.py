"""Implement fixed-size and structure-aware chunking strategies with full traceability."""
from __future__ import annotations

import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split page text into fixed-size character windows with overlap."""
    text = page.text.strip()
    if not text:
        return []

    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    start = 0
    chunk_idx = 0

    while start < len(text):
        end = min(len(text), start + size)
        chunk_text = text[start:end].strip()

        if chunk_text:
            chunk_id = f"{page.document_id}_p{page.page}_fixed_{chunk_idx:03d}"
            # Copy page metadata and attach strategy info
            chunk_meta = dict(page.metadata)
            chunk_meta.update({
                "strategy": "A_fixed",
                "chunk_index": chunk_idx,
                "char_length": len(chunk_text),
                "section": page.metadata.get("section", "khac"),
            })

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata=chunk_meta,
                )
            )
            chunk_idx += 1

        if end >= len(text):
            break
        start += step

    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 800) -> list[Chunk]:
    """Split page text by paragraphs, group short paragraphs, and split oversized paragraphs."""
    raw_text = page.text.strip()
    if not raw_text:
        return []

    # Paragraphs separated by double newline
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_text) if p.strip()]
    if not raw_paragraphs:
        return []

    chunks: list[Chunk] = []
    current_group: list[str] = []
    current_len = 0
    chunk_idx = 0

    def flush_group():
        nonlocal current_group, current_len, chunk_idx
        if not current_group:
            return
        combined_text = "\n\n".join(current_group).strip()
        if combined_text:
            chunk_id = f"{page.document_id}_p{page.page}_para_{chunk_idx:03d}"
            chunk_meta = dict(page.metadata)
            chunk_meta.update({
                "strategy": "B_paragraph",
                "chunk_index": chunk_idx,
                "char_length": len(combined_text),
                "section": page.metadata.get("section", "khac"),
            })
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=combined_text,
                    metadata=chunk_meta,
                )
            )
            chunk_idx += 1
        current_group = []
        current_len = 0

    for para in raw_paragraphs:
        para_len = len(para)
        # If single paragraph is oversized, flush current group and split the paragraph
        if para_len > max_size:
            flush_group()
            # Split oversized paragraph by sentences, semicolons or spaces
            sentences = [s.strip() for s in re.split(r"(?<=[.!?;\n])\s+", para) if s.strip()]
            sub_group: list[str] = []
            sub_len = 0
            for sent in sentences:
                # If even a single sentence exceeds max_size, split by words
                if len(sent) > max_size:
                    if sub_group:
                        sub_text = " ".join(sub_group).strip()
                        chunk_id = f"{page.document_id}_p{page.page}_para_{chunk_idx:03d}"
                        chunk_meta = dict(page.metadata)
                        chunk_meta.update({
                            "strategy": "B_paragraph",
                            "chunk_index": chunk_idx,
                            "char_length": len(sub_text),
                            "section": page.metadata.get("section", "khac"),
                        })
                        chunks.append(
                            Chunk(
                                chunk_id=chunk_id,
                                document_id=page.document_id,
                                source=page.source,
                                page=page.page,
                                text=sub_text,
                                metadata=chunk_meta,
                            )
                        )
                        chunk_idx += 1
                        sub_group = []
                        sub_len = 0
                    words = sent.split()
                    w_group: list[str] = []
                    w_len = 0
                    for w in words:
                        if w_len + len(w) + 1 > max_size and w_group:
                            w_text = " ".join(w_group).strip()
                            chunk_id = f"{page.document_id}_p{page.page}_para_{chunk_idx:03d}"
                            chunk_meta = dict(page.metadata)
                            chunk_meta.update({
                                "strategy": "B_paragraph",
                                "chunk_index": chunk_idx,
                                "char_length": len(w_text),
                                "section": page.metadata.get("section", "khac"),
                            })
                            chunks.append(
                                Chunk(
                                    chunk_id=chunk_id,
                                    document_id=page.document_id,
                                    source=page.source,
                                    page=page.page,
                                    text=w_text,
                                    metadata=chunk_meta,
                                )
                            )
                            chunk_idx += 1
                            w_group = [w]
                            w_len = len(w)
                        else:
                            w_group.append(w)
                            w_len += len(w) + 1
                    if w_group:
                        sub_group = [" ".join(w_group)]
                        sub_len = len(sub_group[0])
                elif sub_len + len(sent) > max_size and sub_group:
                    sub_text = " ".join(sub_group).strip()
                    chunk_id = f"{page.document_id}_p{page.page}_para_{chunk_idx:03d}"
                    chunk_meta = dict(page.metadata)
                    chunk_meta.update({
                        "strategy": "B_paragraph",
                        "chunk_index": chunk_idx,
                        "char_length": len(sub_text),
                        "section": page.metadata.get("section", "khac"),
                    })
                    chunks.append(
                        Chunk(
                            chunk_id=chunk_id,
                            document_id=page.document_id,
                            source=page.source,
                            page=page.page,
                            text=sub_text,
                            metadata=chunk_meta,
                        )
                    )
                    chunk_idx += 1
                    sub_group = [sent]
                    sub_len = len(sent)
                else:
                    sub_group.append(sent)
                    sub_len += len(sent) + 1
            if sub_group:
                sub_text = " ".join(sub_group).strip()
                chunk_id = f"{page.document_id}_p{page.page}_para_{chunk_idx:03d}"
                chunk_meta = dict(page.metadata)
                chunk_meta.update({
                    "strategy": "B_paragraph",
                    "chunk_index": chunk_idx,
                    "char_length": len(sub_text),
                    "section": page.metadata.get("section", "khac"),
                })
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        document_id=page.document_id,
                        source=page.source,
                        page=page.page,
                        text=sub_text,
                        metadata=chunk_meta,
                    )
                )
                chunk_idx += 1
        else:
            # Paragraph fits; check if it fits in current group
            if current_len + para_len + 2 <= max_size:
                current_group.append(para)
                current_len += para_len + 2
            else:
                flush_group()
                current_group.append(para)
                current_len = para_len

    flush_group()
    return chunks
