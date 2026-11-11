"""Independent PR #50 contract probes, drafted before reading the author tests.

These assert sentence selection, exact-body containment, occurrence uniqueness,
and source-relative offsets. They do not assess whether text supports a claim.
"""

from __future__ import annotations

import copy

import pytest

from biotech_rag_assistant.citation_spans import select_enclosing_sentence


@pytest.mark.parametrize(
    ("body", "quote", "expected"),
    [
        (
            "Context only. QA must hold the lot until the owner approves release. Other text.",
            "hold the lot",
            "QA must hold the lot until the owner approves release.",
        ),
        (
            "Context only. QA must hold the lot until the owner approves release. Other text.",
            "QA must hold the lot until the owner approves release.",
            "QA must hold the lot until the owner approves release.",
        ),
        ("Read the report. Keep this final line", "this final", "Keep this final line"),
        ("First.\r\nαβ: QA holds lot β until owner approval.\r\nLast.",
         "lot β", "αβ: QA holds lot β until owner approval."),
        ("Concentration is 2.5 mg per unit. Other.", "2.5 mg", "Concentration is 2.5 mg per unit."),
    ],
)
def test_unique_quote_selects_exact_sentence(body: str, quote: str, expected: str) -> None:
    result = select_enclosing_sentence(body, quote)
    assert result.outcome == "selected"
    assert result.text == expected
    assert result.start is not None and result.end is not None
    assert 0 <= result.start < result.end <= len(body)
    assert body[result.start:result.end] == result.text
    assert quote in result.text


@pytest.mark.parametrize("quote", ["", "absent", "HEADER_ONLY", "STALE_ONLY", "HELD_OUT_ONLY"])
def test_missing_or_external_quote_fails_closed(quote: str) -> None:
    result = select_enclosing_sentence("QA holds the lot pending approval.", quote)
    assert result.model_dump() == {
        "outcome": "not_found", "text": None, "start": None, "end": None,
    }


@pytest.mark.parametrize(
    ("body", "quote"),
    [
        ("QA approval is required. QA approval is recorded.", "QA approval"),
        ("QA approves after QA reviews.", "QA"),
        ("Notify QA QA QA before release.", "QA QA"),
        ("The repeat is CAGCAGCAG.", "CAGCAG"),
        ("aaaaa.", "aaa"),
    ],
)
def test_repeated_quote_is_ambiguous_including_overlapping_occurrences(
    body: str, quote: str,
) -> None:
    occurrences = [index for index in range(len(body)) if body.startswith(quote, index)]
    assert len(occurrences) > 1
    result = select_enclosing_sentence(body, quote)
    assert result.model_dump() == {
        "outcome": "ambiguous", "text": None, "start": None, "end": None,
    }


@pytest.mark.parametrize(
    ("body", "quote", "expected"),
    [
        ("QA must approve! Operators may proceed.", "QA must approve!", "QA must approve!"),
        ("Is QA approval recorded? Operators must verify.", "Is QA approval recorded?",
         "Is QA approval recorded?"),
        ('The label says "Hold." QA must approve release.', 'The label says "Hold."',
         'The label says "Hold."'),
        ("Hold until 5 p.m. unless QA grants an exception. Retain the record.",
         "Hold until 5 p.m. unless QA grants an exception.",
         "Hold until 5 p.m. unless QA grants an exception."),
        ("Hold until 5 p.m. unless QA grants an exception. Retain the record.",
         "Hold until", "Hold until 5 p.m. unless QA grants an exception."),
        ("Dr. Vale must approve release. Retain the record.",
         "must approve release", "Dr. Vale must approve release."),
        ("\n  QA must approve release. Retain the record.",
         "QA must approve release.", "QA must approve release."),
    ],
)
def test_complete_sentences_remain_stable_and_do_not_gain_neighbors(
    body: str, quote: str, expected: str,
) -> None:
    result = select_enclosing_sentence(body, quote)
    assert result.outcome == "selected"
    assert result.text == expected
    assert result.start is not None and result.end is not None
    assert body[result.start:result.end] == result.text


def test_cross_sentence_quote_fails_closed() -> None:
    result = select_enclosing_sentence("QA approves. Operations releases.", "approves. Operations")
    assert result.outcome == "not_found"
    assert result.text is None and result.start is None and result.end is None


def test_authorized_body_offsets_compose_with_unchanged_source_identity() -> None:
    authorized_body = "Context only. QA holds lot β until approval. Keep the record."
    source = {
        "doc_id": "APPROVED-001", "version": "2.0", "status": "Approved",
        "source_hash": "immutable-hash", "source_file_path": "approved.md",
        "raw_text": "# HEADER_ONLY\n\n" + authorized_body + "\n\nSTALE_ONLY HELD_OUT_ONLY",
    }
    before = copy.deepcopy(source)
    body_start = source["raw_text"].index(authorized_body)
    result = select_enclosing_sentence(authorized_body, "lot β")
    assert result.outcome == "selected"
    assert result.text == "QA holds lot β until approval."
    assert result.start is not None and result.end is not None
    assert source["raw_text"][body_start + result.start:body_start + result.end] == result.text
    assert source == before
    assert all(x not in result.text for x in ["HEADER_ONLY", "STALE_ONLY", "HELD_OUT_ONLY"])
