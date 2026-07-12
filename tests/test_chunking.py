"""Direct unit tests for deterministic chunking and the provenance span invariant.

Chunking is the provenance core: the cited offsets are what an auditor slices the source at,
so the central invariant is that ``chunk.text`` is byte-identical to ``raw[char_start:char_end]``
(ADR-016). These tests pin that on the real synthetic corpus rather than testing it indirectly
through retrieval/answer.
"""

from __future__ import annotations

import re
from pathlib import Path

from biotech_rag_assistant.chunking import chunk_document, chunk_documents
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import index_text

CORPUS = Path(__file__).resolve().parents[1] / "examples/synthetic-controlled-docs"


def _corpus():
    return load_corpus(CORPUS)


def test_chunk_text_is_byte_identical_to_cited_span() -> None:
    """text == raw[char_start:char_end] for every chunk — the ADR-016 provenance invariant."""
    corpus = _corpus()
    checked = 0
    for document in corpus.retrievable_documents:
        raw = document.raw_text
        for chunk in chunk_document(document):
            assert chunk.text == raw[chunk.char_start : chunk.char_end]
            checked += 1
    assert checked > 0


def test_index_text_combines_heading_then_span() -> None:
    """The indexed/gated string is heading + span; the heading is not folded into text."""
    corpus = _corpus()
    for chunk in chunk_documents(corpus.documents):
        assert index_text(chunk) == f"{chunk.section_heading}\n{chunk.text}"
        assert index_text(chunk).startswith(chunk.section_heading)


def test_heading_is_not_part_of_the_cited_span() -> None:
    """Regression for the pre-ADR-016 bug: the quote no longer carries the prepended heading."""
    chunks = {c.chunk_id: c for c in chunk_documents(_corpus().documents)}
    chunk = chunks["CAL-ENG-005_v1_0_chunk_001"]
    assert chunk.section_heading == "Daily check"
    # The body span starts with the body, not the heading line.
    assert not chunk.text.startswith(chunk.section_heading)
    assert chunk.text.startswith("The analyst verifies")


def test_only_retrievable_documents_are_chunked() -> None:
    """Draft/obsolete documents never reach the index (status gate lives inside chunking)."""
    chunks = chunk_documents(_corpus().documents)
    statuses = {chunk.status for chunk in chunks}
    assert statuses <= {"Approved", "Effective"}
    chunked_doc_ids = {chunk.doc_id for chunk in chunks}
    # SOP-QA-009 is Obsolete and SOP-QA-010 is Draft in the synthetic corpus.
    assert "SOP-QA-009" not in chunked_doc_ids
    assert "SOP-QA-010" not in chunked_doc_ids


def test_chunk_ids_are_deterministic_and_version_scoped() -> None:
    corpus = _corpus()
    first = chunk_documents(corpus.documents)
    second = chunk_documents(corpus.documents)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert [c.text for c in first] == [c.text for c in second]
    id_pattern = re.compile(r"^.+_v.+_chunk_\d{3}$")
    for chunk in first:
        assert id_pattern.match(chunk.chunk_id)
        safe_version = re.sub(r"[^A-Za-z0-9]+", "_", chunk.version).strip("_")
        assert chunk.chunk_id == f"{chunk.doc_id}_v{safe_version}_chunk_{chunk.chunk_index:03d}"


def test_chunk_indices_are_sequential_per_document() -> None:
    corpus = _corpus()
    for document in corpus.retrievable_documents:
        indices = [chunk.chunk_index for chunk in chunk_document(document)]
        assert indices == list(range(1, len(indices) + 1))


def test_offsets_are_valid_and_non_overlapping_within_a_document() -> None:
    corpus = _corpus()
    for document in corpus.retrievable_documents:
        previous_end = 0
        for chunk in chunk_document(document):
            assert chunk.char_end > chunk.char_start
            assert chunk.char_start >= previous_end
            previous_end = chunk.char_end
