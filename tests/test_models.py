"""Direct unit tests for the typed trust-layer records.

These pin the fail-closed validators the rest of the system relies on: the sha256 hash format,
the corpus hash-match guard, chunk offset ordering, the review-date rule, the status->retrievable
mapping, and ``extra="forbid"`` rejecting unknown fields.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from biotech_rag_assistant.models import DocumentChunk, DocumentMetadata, SourceDocument

VALID_HASH = "sha256:" + "a" * 64
OTHER_HASH = "sha256:" + "b" * 64

VALID_META = {
    "doc_id": "SOP-QA-001",
    "doc_title": "Environmental Monitoring",
    "doc_type": "SOP",
    "version": "1.0",
    "status": "Approved",
    "effective_date": "2026-01-01",
    "department": "Quality",
    "source_file_path": "documents/sop.md",
    "source_hash": VALID_HASH,
}


def _chunk(**overrides):
    payload = {
        "chunk_id": "SOP-QA-001_v1_0_chunk_001",
        "doc_id": "SOP-QA-001",
        "doc_title": "Environmental Monitoring",
        "doc_type": "SOP",
        "version": "1.0",
        "status": "Approved",
        "department": "Quality",
        "section_heading": "Scope",
        "source_file_path": Path("documents/sop.md"),
        "source_hash": VALID_HASH,
        "chunk_index": 1,
        "line_or_page_span": "lines 1-2",
        "char_start": 0,
        "char_end": 5,
        "text": "hello",
    }
    payload.update(overrides)
    return DocumentChunk(**payload)


def test_valid_metadata_loads() -> None:
    meta = DocumentMetadata.model_validate(VALID_META)
    assert meta.is_retrievable is True


@pytest.mark.parametrize("bad_hash", ["abc", "sha256:" + "a" * 63, "md5:" + "a" * 64, "a" * 64])
def test_source_hash_format_is_enforced(bad_hash: str) -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata.model_validate({**VALID_META, "source_hash": bad_hash})


def test_review_due_date_before_effective_is_rejected() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata.model_validate(
            {**VALID_META, "effective_date": "2026-01-01", "review_due_date": "2025-12-31"}
        )


def test_unknown_metadata_field_is_forbidden() -> None:
    with pytest.raises(ValidationError):
        DocumentMetadata.model_validate({**VALID_META, "classification": "secret"})


@pytest.mark.parametrize(
    "status,retrievable",
    [
        ("Approved", True),
        ("Effective", True),
        ("Draft", False),
        ("Obsolete", False),
        ("Superseded", False),
    ],
)
def test_is_retrievable_follows_status(status: str, retrievable: bool) -> None:
    meta = DocumentMetadata.model_validate({**VALID_META, "status": status})
    assert meta.is_retrievable is retrievable


def test_source_document_requires_matching_hash() -> None:
    meta = DocumentMetadata.model_validate(VALID_META)
    with pytest.raises(ValidationError):
        SourceDocument(
            metadata_path=Path("m.yaml"),
            content_path=Path("c.md"),
            raw_text="body",
            computed_source_hash=OTHER_HASH,
            metadata=meta,
        )


def test_source_document_loads_when_hash_matches() -> None:
    meta = DocumentMetadata.model_validate(VALID_META)
    document = SourceDocument(
        metadata_path=Path("m.yaml"),
        content_path=Path("c.md"),
        raw_text="body",
        computed_source_hash=VALID_HASH,
        metadata=meta,
    )
    assert document.is_retrievable is True


def test_valid_chunk_builds() -> None:
    assert _chunk().char_end == 5


@pytest.mark.parametrize("char_start,char_end", [(5, 5), (5, 3)])
def test_chunk_offsets_must_increase(char_start: int, char_end: int) -> None:
    with pytest.raises(ValidationError):
        _chunk(char_start=char_start, char_end=char_end)


def test_chunk_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        _chunk(confidence=0.9)
