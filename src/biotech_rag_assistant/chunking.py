"""Deterministic Markdown/text chunking for the retrieval pilot."""

from __future__ import annotations

import re
from dataclasses import dataclass

from biotech_rag_assistant.models import DocumentChunk, SourceDocument

HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class PendingParagraph:
    start_line: int
    end_line: int
    lines: list[str]
    section_heading: str


def chunk_documents(documents: list[SourceDocument]) -> list[DocumentChunk]:
    """Chunk retrievable documents in deterministic document order."""
    chunks: list[DocumentChunk] = []
    for document in documents:
        if document.is_retrievable:
            chunks.extend(chunk_document(document))
    return chunks


def chunk_document(document: SourceDocument) -> list[DocumentChunk]:
    """Split one source into paragraph chunks with source line spans."""
    lines = document.raw_text.splitlines()
    line_offsets = _line_offsets(document.raw_text)
    section_heading = document.metadata.doc_title
    pending: list[str] = []
    pending_start: int | None = None
    paragraphs: list[PendingParagraph] = []

    def flush(end_line: int) -> None:
        nonlocal pending, pending_start
        if pending_start is None:
            return
        text_lines = [line for line in pending if line.strip()]
        if text_lines:
            paragraphs.append(
                PendingParagraph(
                    start_line=pending_start,
                    end_line=end_line,
                    lines=text_lines,
                    section_heading=section_heading,
                )
            )
        pending = []
        pending_start = None

    for line_number, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush(line_number - 1)
            section_heading = heading_match.group(2).strip()
            continue

        if not line.strip():
            flush(line_number - 1)
            continue

        if pending_start is None:
            pending_start = line_number
        pending.append(line)

    flush(len(lines))

    chunks: list[DocumentChunk] = []
    for index, paragraph in enumerate(paragraphs, start=1):
        char_start = line_offsets[paragraph.start_line - 1]
        last_line_text = lines[paragraph.end_line - 1] if paragraph.end_line > 0 else ""
        char_end = line_offsets[paragraph.end_line - 1] + len(last_line_text)
        # The chunk text is the verbatim source span the citation points at, byte-for-byte:
        # text == raw_text[char_start:char_end] (ADR-016). The section heading is combined only
        # at index/scoring time (retrieval.index_text), so it stays matchable for retrieval
        # without making the cited quote disagree with its own offsets.
        span_text = document.raw_text[char_start:char_end]
        chunks.append(
            DocumentChunk(
                chunk_id=_chunk_id(document, index),
                doc_id=document.metadata.doc_id,
                doc_title=document.metadata.doc_title,
                doc_type=document.metadata.doc_type,
                version=document.metadata.version,
                status=document.metadata.status,
                department=document.metadata.department,
                section_heading=paragraph.section_heading,
                source_file_path=document.metadata.source_file_path,
                source_hash=document.metadata.source_hash,
                chunk_index=index,
                line_or_page_span=f"lines {paragraph.start_line}-{paragraph.end_line}",
                char_start=char_start,
                char_end=char_end,
                text=span_text,
            )
        )
    return chunks


def _line_offsets(text: str) -> list[int]:
    offsets: list[int] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        offsets.append(offset)
        offset += len(line)
    if not offsets and text:
        offsets.append(0)
    return offsets


def _chunk_id(document: SourceDocument, chunk_index: int) -> str:
    safe_version = re.sub(r"[^A-Za-z0-9]+", "_", document.metadata.version).strip("_")
    return f"{document.metadata.doc_id}_v{safe_version}_chunk_{chunk_index:03d}"
