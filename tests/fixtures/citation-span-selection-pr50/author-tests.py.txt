from __future__ import annotations

import hashlib
from pathlib import Path

from biotech_rag_assistant.citation_spans import select_enclosing_sentence

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "examples/synthetic-controlled-docs/documents/SOP-OPS-007-line-clearance.md"
CAL = ROOT / "examples/synthetic-controlled-docs/documents/CAL-ENG-005-balance-calibration.md"
SOURCE_SHA256 = "ad866150db306fbf8eaaab555acb8c661a203d34b42e62f4e510f3efff270735"
BODY_START = 213
BODY_END = 415
HISTORICAL_QUOTE = "both operations and QA sign the clearance record"
ARM_B = "The run cannot start until both operations and QA sign the clearance record."
HELD_OUT_SPAN = "Daily balance checks are logged on FRM-QC-141."


def _sop() -> str:
    raw = SOP.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA256
    return raw.decode("utf-8")


def test_historical_a08_quote_expands_to_the_supporting_sentence() -> None:
    document = _sop()
    body = document[BODY_START:BODY_END]
    selected = select_enclosing_sentence(body, HISTORICAL_QUOTE)

    assert selected.outcome == "selected"
    assert selected.text == ARM_B
    assert body[selected.start : selected.end] == ARM_B
    assert selected.text in body
    assert "Independent check" not in selected.text
    assert HELD_OUT_SPAN not in selected.text


def test_full_sentence_quote_does_not_grow() -> None:
    body = _sop()[BODY_START:BODY_END]
    selected = select_enclosing_sentence(body, ARM_B)

    assert selected.outcome == "selected"
    assert selected.text == ARM_B
    assert len(selected.text) - len(ARM_B) == 0


def test_other_sentence_is_not_pulled_in() -> None:
    body = _sop()[BODY_START:BODY_END]
    selected = select_enclosing_sentence(body, "room readiness")

    assert selected.outcome == "selected"
    assert selected.text is not None
    assert selected.text.startswith("QA performs an independent line clearance check")
    assert HISTORICAL_QUOTE not in selected.text


def test_missing_and_repeated_quotes_are_refused() -> None:
    body = _sop()[BODY_START:BODY_END]

    assert select_enclosing_sentence(body, HELD_OUT_SPAN).outcome == "not_found"
    assert select_enclosing_sentence(body, "").outcome == "not_found"
    repeated = select_enclosing_sentence(body + " " + body, HISTORICAL_QUOTE)
    assert repeated.outcome == "ambiguous"
    assert repeated.text is None


def test_selection_stays_inside_the_supplied_body() -> None:
    document = _sop()
    selected = select_enclosing_sentence(document, HISTORICAL_QUOTE)

    assert selected.outcome == "selected"
    assert selected.start == 339
    assert selected.end == 415
    assert document[selected.start : selected.end] == selected.text
    # A different authorized document is not consulted.
    other = CAL.read_text()
    assert select_enclosing_sentence(other, HISTORICAL_QUOTE).outcome == "not_found"
