from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import pytest

from biotech_rag_assistant.citation_spans import select_enclosing_sentence, sentence_spans

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "tests/fixtures/citation-span-selection-pr50"


@pytest.mark.parametrize(
    ("path", "digest"),
    [
        ("tests/test_citation_spans_pr50_author.py",
         "67751c42f918f32cea35bc6bd86e3bddd0a9ea7574376865e1ed82cd6078414d"),
        ("tests/test_citation_spans_pr50_independent.py",
         "48818936a0b317d23eed48ef507e9516bb0de9c67cf29a02592338175711444a"),
        ("tests/fixtures/citation-span-selection-pr50/source-citation-spans.py.txt",
         "f2d55d054c0a06b8bfd8af775ade8da09953b83529b29e8672588d25421ef9fa"),
        ("tests/fixtures/citation-span-selection-pr50/counterexamples.json",
         "fdb9439935551bb0c7cbcee9bee75a89cc12e63c39b5021a7b8813a5aaf54fd8"),
    ],
)
def test_rejected_candidate_and_historical_tests_preserve_original_bytes(
    path: str, digest: str,
) -> None:
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_archived_limiting_condition_is_retained() -> None:
    cases = json.loads((ARCHIVE / "counterexamples.json").read_text())["cases"]
    case = next(case for case in cases if case["case"] == "abbreviation_truncates_condition")
    result = select_enclosing_sentence(case["body"], case["quote"])
    assert case["result"]["text"] == "Release is allowed for lot No."
    assert result.outcome == "selected"
    assert result.text == case["body"]
    assert result.text.endswith("only after QA approval.")
    assert result.start == 0 and result.end == len(case["body"])


@pytest.mark.parametrize(
    ("body", "quote", "expected"),
    [
        ("Hold for lot No. 7 only after approval. Keep the record.", "Hold for",
         "Hold for lot No. 7 only after approval."),
        ("Dr. Vale must approve release. Keep the record.", "must approve",
         "Dr. Vale must approve release."),
        ("Wait until 5 p.m. unless QA permits release. Keep the record.", "Wait until",
         "Wait until 5 p.m. unless QA permits release."),
        ("Wait until 7 a.m. before recording results. Keep the record.", "before recording",
         "Wait until 7 a.m. before recording results."),
        ("Verify αβ concentration is 2.5 mg. Keep the record.", "2.5 mg",
         None),  # A short terminal unit is deliberately uncertain before more text.
        ("Verify αβ concentration is 2.5 mg per unit. Keep the record.", "2.5 mg",
         "Verify αβ concentration is 2.5 mg per unit."),
        ("\r\n\tQA can't release without approval.  ", "can't release",
         "QA can't release without approval."),
        ('The label says "Hold." Keep the record.', 'label says',
         'The label says "Hold."'),
    ],
)
def test_documented_boundary_language(
    body: str, quote: str, expected: str | None,
) -> None:
    result = select_enclosing_sentence(body, quote)
    if expected is None:
        assert result.outcome == "boundary_uncertain"
        assert result.text is None and result.start is None and result.end is None
    else:
        assert result.outcome == "selected"
        assert result.text == expected
        assert body[result.start:result.end] == expected


@pytest.mark.parametrize(
    "body",
    [
        "Release is allowed for lot No. X only after approval.",
        "Release is allowed at 5 p.m. Unless approval is absent.",
        "Release is allowed per Ref. 7 only after approval.",
        "Release is allowed per approx. Guidance only after approval.",
        "Release is allowed per XYZ. Protocol only after approval.",
        "Release is allowed per X.Y. only after approval.",
        "Release is allowed. unless approval is absent.",
        "Release is allowed! unless approval is absent.",
        'Release is allowed under "Hold." unless approval is absent.',
        "Release is allowed (only after approval).",
        "Release is allowed [only after approval].",
        "Release is allowed... only after approval.",
        "Release is allowed… only after approval.",
        "Release is allowed。 Only after approval.",
        "Release is allowed!?! Only after approval.",
        "Release is allowed per step 7. Only after approval.",
        "Release is allowed.Only after approval.",
        'Release is allowed under "Hold. Do not proceed."',
        'Release is allowed under "Hold until approval.',
        "Release is allowed under ‘Hold.’ Until approval.",
        "Release is allowed under 'Hold.' Until approval.",
        "Release is allowed\x00 only after approval.",
    ],
)
def test_unsupported_boundaries_never_return_a_truncated_selection(body: str) -> None:
    result = select_enclosing_sentence(body, "Release is allowed")
    assert result.model_dump() == {
        "outcome": "boundary_uncertain", "text": None, "start": None, "end": None,
    }
    assert sentence_spans(body) is None


def test_unsafe_neighbor_refuses_whole_body_without_guessing_local_boundaries() -> None:
    result = select_enclosing_sentence(
        "QA must approve release. Unclear etc. Condition.", "approve"
    )
    assert result.outcome == "boundary_uncertain"


def test_occurrence_uniqueness_matches_independent_overlapping_offset_oracle() -> None:
    # Exhaustive tiny alphabet finds both overlapping and ordinary repetitions;
    # this oracle never uses str.count or the implementation's second-find logic.
    for width in range(1, 7):
        for letters in itertools.product("ab", repeat=width):
            body = "".join(letters) + "."
            for quote_width in range(1, width + 1):
                for quote_start in range(width - quote_width + 1):
                    quote = body[quote_start:quote_start + quote_width]
                    occurrences = sum(body[index:index + len(quote)] == quote
                                      for index in range(len(body)))
                    result = select_enclosing_sentence(body, quote)
                    if occurrences > 1:
                        assert result.outcome == "ambiguous"
                        assert result.text is None
                    else:
                        assert result.outcome == "selected"
                        assert result.text == body


def test_offset_composition_retains_unicode_and_crlf_without_normalization() -> None:
    body = "\r\n  αβ: QA must approve release.\r\nKeep the record.\r\n"
    selected = select_enclosing_sentence(body, "αβ: QA")
    assert selected.outcome == "selected"
    assert selected.start == 4
    assert selected.text == "αβ: QA must approve release."
    source = "# HEADER_ONLY\r\n" + body + "HELD_OUT_ONLY"
    source_body_start = source.index(body)
    source_slice = source[source_body_start + selected.start:source_body_start + selected.end]
    assert source_slice == selected.text


def test_missing_and_ambiguous_take_precedence_over_boundary_uncertainty() -> None:
    body = "[QA QA QA]"
    assert select_enclosing_sentence(body, "absent").outcome == "not_found"
    assert select_enclosing_sentence(body, "QA QA").outcome == "ambiguous"
    assert select_enclosing_sentence(body, " ").outcome == "not_found"
