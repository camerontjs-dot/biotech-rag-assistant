"""Contract tests for literal selection using explicit caller-authorized bounds."""

from __future__ import annotations

import hashlib
import itertools
from pathlib import Path

import pytest

from biotech_rag_assistant.citation_spans import select_authorized_span


def refused(result, outcome):
    assert result.model_dump() == {
        "outcome": outcome, "text": None, "start": None, "end": None,
    }


@pytest.mark.parametrize(
    ("body", "quote", "start", "end"),
    [
        ("First. QA holds the lot until approval. Last.", "the lot", 7, 38),
        ("αβ 🧬: QA approves.", "QA", 0, 17),
        ("  Exact BODY text.  ", "BODY", 0, 20),
        ("Header\n\nQA signs.\n\nOther section", "QA signs", 8, 17),
        ("QA may release\r\nonly after approval.", "only after", 0, 35),
    ],
)
def test_explicit_range_returns_exact_unmodified_slice(body, quote, start, end):
    result = select_authorized_span(body, quote, authorized_start=start, authorized_end=end)
    assert result.outcome == "selected"
    assert result.model_dump() == {
        "outcome": "selected", "text": body[start:end], "start": start, "end": end,
    }


@pytest.mark.parametrize("body", [
    "Release is allowed for lot No. 7 only after QA approval.",
    "Release is allowed only after Coord. Smith signs the authorization.",
    "Release is allowed only after Prof. Vale signs.",
    "Release is allowed until 5 p.m. unless QA grants an exception.",
    "Release is allowed!", "Release is allowed", "Release is allowed. Other text.",
])
def test_no_bounds_never_guesses_a_sentence(body):
    refused(select_authorized_span(body, "Release is allowed"), "bounds_required")


@pytest.mark.parametrize("quote", ["", " ", "\t\n", "absent", "HEADING_ONLY", "STALE_ONLY"])
def test_absent_quote_cannot_be_authorized_with_offsets(quote):
    refused(select_authorized_span("QA holds the lot.", quote,
                                  authorized_start=0, authorized_end=17), "not_found")


@pytest.mark.parametrize(("body", "quote"), [
    ("Notify QA QA QA before release.", "QA QA"),
    ("aaaaa", "aaa"), ("CAGCAGCAG", "CAGCAG"),
    ("QA approves. QA records.", "QA"), ("ééé", "éé"),
])
def test_global_ambiguity_is_not_resolved_by_narrow_bounds(body, quote):
    refused(select_authorized_span(body, quote, authorized_start=0,
                                  authorized_end=len(quote)), "ambiguous")


@pytest.mark.parametrize(("start", "end"), [
    (None, 5), (0, None), (-1, 5), (5, 3), (2, 2), (0, 99),
    (True, 5), (False, 5), (0, True), (0.0, 5), (0, 5.0),
    ("0", 5), (0, "5"), ([], 5), (0, {}),
])
def test_invalid_bound_types_and_ranges_refuse(start, end):
    refused(select_authorized_span("QA signs.", "QA", authorized_start=start,
                                  authorized_end=end), "invalid_bounds")


@pytest.mark.parametrize(("start", "end"), [(0, 1), (1, 7), (3, 7), (2, 6)])
def test_range_must_contain_the_entire_unique_quote(start, end):
    refused(select_authorized_span("A QA signs.", "QA signs", authorized_start=start,
                                  authorized_end=end), "invalid_bounds")


@pytest.mark.parametrize("separator", ["\n\n", "\r\n\r\n", "\r\r", "\n \t\n", "\u2029"])
def test_authorized_slice_must_not_cross_a_paragraph(separator):
    body = "Release is allowed" + separator + "only after approval."
    refused(select_authorized_span(body, "Release is allowed", authorized_start=0,
                                  authorized_end=len(body)), "invalid_bounds")


def test_supplied_bounds_are_a_precondition_not_a_semantic_verdict():
    body = "Release is allowed only after Coord. Smith signs."
    # Deliberately incomplete caller authority remains a caller error. This
    # utility must neither silently repair it nor call it a complete sentence.
    end = body.index(" Smith")
    result = select_authorized_span(body, "Release is allowed", authorized_start=0,
                                    authorized_end=end)
    assert result.outcome == "selected"
    assert result.text == body[:end]
    assert set(result.model_dump()) == {"outcome", "text", "start", "end"}


def test_a08_previously_authorized_span_preserves_source_coordinates():
    authorized = "The run cannot start until both operations and QA sign the clearance record."
    body = "Record clearance first. " + authorized + " Retain the record."
    start = len("Record clearance first. ")
    quote = "both operations and QA sign the clearance record"
    result = select_authorized_span(body, quote, authorized_start=start,
                                    authorized_end=start + len(authorized))
    assert result.outcome == "selected"
    assert result.text == authorized
    assert len(authorized) == 76


def test_overlap_decision_matches_exhaustive_oracle():
    for length in range(1, 7):
        for letters in itertools.product("ab", repeat=length):
            body = "".join(letters)
            for size in range(1, 4):
                for needle in itertools.product("ab", repeat=size):
                    quote = "".join(needle)
                    count = sum(body.startswith(quote, i) for i in range(len(body)))
                    expected = (
                        "not_found" if count == 0 else "ambiguous" if count > 1 else "selected"
                    )
                    result = select_authorized_span(body, quote, authorized_start=0,
                                                    authorized_end=len(body))
                    assert result.outcome == expected


def test_historical_pr50_artifact_bytes_are_preserved():
    root = Path(__file__).parent / "fixtures/citation-span-selection-pr50"
    expected = {
        "source-citation-spans.py.txt": (
            "f2d55d054c0a06b8bfd8af775ade8da09953b83529b29e8672588d25421ef9fa"
        ),
        "author-tests.py.txt": "67751c42f918f32cea35bc6bd86e3bddd0a9ea7574376865e1ed82cd6078414d",
        "independent-probes.py.txt": (
            "48818936a0b317d23eed48ef507e9516bb0de9c67cf29a02592338175711444a"
        ),
        "counterexamples.json": "fdb9439935551bb0c7cbcee9bee75a89cc12e63c39b5021a7b8813a5aaf54fd8",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
