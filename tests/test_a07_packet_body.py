from __future__ import annotations

from pathlib import Path

from research.a07_packet_body import HISTORICAL_BODY, MISSING_PROPOSITION, evaluate

ROOT = Path(__file__).resolve().parents[1]


def test_same_section_expansion_adds_no_body_and_misses_the_proposition() -> None:
    result = evaluate(ROOT)
    candidate = result["candidate"]

    assert candidate["text"] == HISTORICAL_BODY
    assert candidate["characters_added"] == 0
    assert candidate["spans_added"] == 0
    assert candidate["proposition_present"] is False
    assert MISSING_PROPOSITION not in candidate["text"].casefold()
    assert result["disposition"] == "SAME_SECTION_BODY_EXPANSION_NOT_SUPPORTED"
    assert result["model_calls"] == 0


def test_heading_is_not_used_and_next_section_stays_out() -> None:
    result = evaluate(ROOT)
    heading = result["heading"]
    negative = result["negative_control"]

    assert heading["text"] == "Daily check"
    assert heading["contains_daily_token"] is True
    assert heading["used_as_support"] is False
    assert heading["added_text_excluded_heading"] is True
    assert negative["states_missing_proposition"] is False
    assert negative["next_section_admitted"] is False
    assert "Engineering reviews the failure" in negative["next_section_text"]
    assert result["falsifiers"]["supported_only_by_heading"] is False
    assert result["falsifiers"]["retrieval_or_reranker_changed"] is False


def test_held_out_and_stale_spans_are_not_admitted() -> None:
    result = evaluate(ROOT)
    trap = result["authority_trap"]

    assert trap["authorized_span_admitted"] is True
    assert trap["held_out_admitted"] is False
    assert trap["stale_admitted"] is False
    assert trap["held_out"]["doc_id"] == "CAL-0507"
    assert trap["held_out"]["span"] == "Daily balance checks are logged on FRM-QC-141."
    assert trap["stale"]["status"] == "Obsolete"
    assert result["falsifiers"]["stale_or_held_out_admitted"] is False
    assert result["falsifiers"]["source_identity_unreconstructed"] is False
    assert result["inherited_judgment"]["terminal"] == "PACKET_LEVEL_GROUNDING_DEFECT"
