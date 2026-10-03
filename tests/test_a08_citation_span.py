from __future__ import annotations

from pathlib import Path

from research.a08_citation_span import (
    BODY_END,
    BODY_START,
    FROZEN_BODY,
    HEADING_EXCLUDED,
    HISTORICAL_QUOTE,
    evaluate,
)

ROOT = Path(__file__).resolve().parents[1]


def test_arm_b_is_the_supporting_sentence_inside_the_frozen_body() -> None:
    result = evaluate(ROOT)
    arm_b = result["arm_b"]
    observations = result["observations"]

    assert arm_b["text"] == (
        "The run cannot start until both operations and QA sign the clearance record."
    )
    assert arm_b["char_start"] == 339
    assert arm_b["char_end"] == 415
    assert observations["arm_a_exact_substring_of_arm_b"]
    assert observations["arm_b_contained_in_frozen_supported_body"]
    assert observations["character_increase"] == len(arm_b["text"]) - len(HISTORICAL_QUOTE)
    assert observations["added_prefix"] == "The run cannot start until "
    assert observations["added_suffix"] == "."
    assert observations["quote_occurrences_in_body"] == 1
    assert result["disposition"] == "BOUNDED_CITATION_SPAN_EXPANSION_SUPPORTED"
    assert result["model_calls"] == 0


def test_packet_source_and_heading_stay_fixed() -> None:
    result = evaluate(ROOT)
    held = result["held_fixed"]
    observations = result["observations"]
    falsifiers = result["falsifiers"]

    assert held["chunk_id"] == "SOP-OPS-007_v1_2_chunk_002"
    assert held["source_sha256"] == (
        "ad866150db306fbf8eaaab555acb8c661a203d34b42e62f4e510f3efff270735"
    )
    assert held["body_char_start"] == BODY_START
    assert held["body_char_end"] == BODY_END
    source = ROOT / "examples/synthetic-controlled-docs/documents"
    document = (source / "SOP-OPS-007-line-clearance.md").read_text()
    assert document[BODY_START:BODY_END] == FROZEN_BODY
    assert HEADING_EXCLUDED not in result["arm_b"]["text"]
    assert observations["packet_membership_changed"] is False
    assert observations["new_source_required"] is False
    assert falsifiers == {
        "requires_new_packet_evidence": False,
        "imports_heading_semantics": False,
        "source_identity_changed": False,
        "expansion_leaves_quote_ambiguous_inside_body": False,
        "cannot_distinguish_citation_from_packet": False,
    }


def test_historical_quote_is_the_narrower_arm() -> None:
    result = evaluate(ROOT)
    arm_a = result["arm_a"]

    assert arm_a["text"] == HISTORICAL_QUOTE
    assert arm_a["char_start"] == 366
    assert arm_a["char_end"] == 414
    assert result["inherited_judgment"]["q"] == "OVER_BROAD"
    assert result["inherited_judgment"]["n"] == "SUPPORTED"
    assert result["inherited_judgment"]["terminal"] == "CITATION_SPAN_INSUFFICIENCY"
