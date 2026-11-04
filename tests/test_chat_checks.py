"""Mechanical checks on model answers. These are deliberately not semantic-support checks.

A statement is shown only if it cites a supplied passage, its quotation is located verbatim in
that passage, and every number in it appears in the cited passage. The tests also pin what the
checks do *not* establish: a correctly quoted but unsupported paraphrase still passes.
"""

from __future__ import annotations

import pytest
from chat_support import BALANCE_QUESTION, EM_QUESTION, binding_for

from biotech_rag_assistant.chat.checks import AnswerView, check_answer, locate_quote
from biotech_rag_assistant.chat.contract import ModelAnswer
from biotech_rag_assistant.chat.evidence import EvidencePassage, assemble_evidence
from biotech_rag_assistant.chat.resolution import resolve_turn
from biotech_rag_assistant.chat.testing import answer, block, missing_item
from biotech_rag_assistant.retrieval import RetrievalConfig

CONFIG = RetrievalConfig(top_k=3)
BINDING = binding_for()


def evidence(question: str) -> list[EvidencePassage]:
    resolved = resolve_turn(
        question, turn_index=1, active_topic=None, new_topic=False, binding=BINDING, config=CONFIG
    )
    return assemble_evidence(resolved.hit_sets, BINDING, 6)


EM = evidence(EM_QUESTION)
BALANCE = evidence(BALANCE_QUESTION)


def ref_with(passages: list[EvidencePassage], fragment: str) -> str:
    return next(p.ref for p in passages if fragment in p.text)


def check(
    passages: list[EvidencePassage], payload: dict, user_messages: list[str] | None = None
) -> AnswerView:
    return check_answer(
        ModelAnswer.model_validate(payload), passages, user_messages=user_messages or []
    )


S_EM = ref_with(EM, "QA opens a deviation")
S_BAL = ref_with(BALANCE, "acceptance range")


def one(text: str, *citations: tuple[str, str], kind: str = "paragraph") -> dict:
    return answer("answered", [block(kind, text, *citations)])


# --- Shown statements ---


def test_exact_citation_is_shown_with_source_offsets() -> None:
    quote = "QA opens a deviation before product disposition"
    view = check(EM, one("QA opens a deviation first.", (S_EM, quote)))

    shown = view.blocks[0]
    assert not shown.withheld and shown.valid_refs == [S_EM]
    citation = shown.citations[0]
    passage = next(p for p in EM if p.ref == S_EM)
    assert passage.text[citation.highlight_start : citation.highlight_end] == quote
    assert view.support_scope == "mechanical_only"
    assert "does not establish" in view.support_note


def test_quote_location_folds_case_whitespace_and_typographic_marks() -> None:
    text = "QA performs an independent line clearance check for product identity."
    located = locate_quote(text, "  qa   performs an\nindependent ")
    assert located is not None and text[located[0] : located[1]] == "QA performs an independent"
    assert locate_quote("The analyst's log", "the analyst’s log") == (0, 17)


def test_correct_quote_with_unsupported_paraphrase_still_passes() -> None:
    """The documented limit: a real quote does not prove the claim beside it."""
    view = check(
        EM,
        one(
            "QA may skip the deviation if the room looks clean.",
            (S_EM, "QA opens a deviation before product disposition"),
        ),
    )

    assert not view.blocks[0].withheld


# --- Withheld statements ---


def test_invented_citation_ref_is_withheld() -> None:
    view = check(EM, one("QA opens a deviation.", ("S9", "QA opens a deviation before")))

    assert view.blocks[0].withheld
    assert view.unknown_refs == ["S9"]
    assert "not supplied" in (view.blocks[0].withheld_reason or "")
    assert view.blocks[0].text is None
    assert view.blocks[0].withheld_text == "QA opens a deviation."


def test_invented_ref_withholds_even_beside_a_valid_citation() -> None:
    view = check(
        EM,
        one(
            "QA opens a deviation.",
            (S_EM, "QA opens a deviation before product disposition"),
            ("S7", "made up"),
        ),
    )
    assert view.blocks[0].withheld


@pytest.mark.parametrize(
    ("quote", "issue"),
    [
        ("QA closes the deviation after product disposition", "quote_not_in_passage"),
        ("QA opens a deviation ... product disposition", "quote_not_in_passage"),
        ("QA opens", "quote_too_short"),
        ("Immediate containment When viable monitoring", "quote_not_in_passage"),
    ],
)
def test_unlocatable_quote_leaves_no_valid_citation(quote: str, issue: str) -> None:
    view = check(EM, one("QA opens a deviation.", (S_EM, quote)))

    assert view.blocks[0].withheld
    assert view.blocks[0].citations[0].issue == issue


def test_heading_text_cannot_be_quoted_as_evidence() -> None:
    view = check(BALANCE, one("The daily check uses weights.", (S_BAL, "Daily check")))
    assert view.blocks[0].withheld


def test_uncited_statement_is_withheld() -> None:
    view = check(EM, answer("answered", [block("paragraph", "QA handles it.")]))

    assert view.blocks[0].withheld
    assert view.blocks[0].withheld_reason == "It cites no source passage."


def test_one_bad_quote_beside_a_good_one_keeps_the_statement() -> None:
    view = check(
        EM,
        one(
            "QA opens a deviation.",
            (S_EM, "QA opens a deviation before product disposition"),
            (S_EM, "QA files a report within two days"),
        ),
    )

    shown = view.blocks[0]
    assert not shown.withheld
    assert [c.issue for c in shown.citations] == [None, "quote_not_in_passage"]


@pytest.mark.parametrize(
    "fabricated",
    [
        "The acceptance range is ±0.1 mg.",
        "Each weight must read within 0.05% of nominal.",
        "The tolerance is plus or minus five milligrams.",
        "The acceptance range is 99.9 to 100.1 percent.",
    ],
)
def test_invented_value_cited_to_a_real_passage_is_withheld(fabricated: str) -> None:
    """Generation-side counterpart of tests/test_known_gaps.py: the passage names the range only."""
    view = check(BALANCE, one(fabricated, (S_BAL, "If either weight falls outside the acceptance")))

    assert view.blocks[0].withheld
    assert "does not appear in its cited passage" in (view.blocks[0].withheld_reason or "")
    assert view.shown_count == 0


def test_values_stated_by_the_passage_are_shown() -> None:
    quote = "The analyst verifies the balance with two traceable weights before use"
    for text in ("The analyst uses two traceable weights.", "It uses 2 traceable weights."):
        assert not check(BALANCE, one(text, (S_BAL, quote))).blocks[0].withheld


def test_user_supplied_value_is_withheld_and_attributed() -> None:
    view = check(
        BALANCE,
        one("The official acceptance range is 0.5 mg.", (S_BAL, "outside the acceptance range")),
        user_messages=["Our lab uses an acceptance range of 0.5 mg for the daily balance check."],
    )

    reason = view.blocks[0].withheld_reason or ""
    assert view.blocks[0].withheld
    assert "0.5" in reason and "appears in your messages" in reason


def test_identifiers_versions_and_step_numbers_are_not_values() -> None:
    quote = "QA opens a deviation before product disposition"
    for text in (
        "SOP-QA-001 v1.0 requires QA to open a deviation.",
        "1. QA opens a deviation before disposition [S2].",
        "Under version 1.0 of SOP-QA-001, QA opens a deviation.",
    ):
        assert not check(EM, one(text, (S_EM, quote), kind="step")).blocks[0].withheld, text


# --- Advisory notes (never withhold) ---


def test_dropped_condition_is_noted_and_preserved_condition_is_not() -> None:
    quote_a = "When viable monitoring exceeds an action limit, QA opens a deviation before product"
    dropped = check(EM, one("QA opens a deviation before product disposition.", (S_EM, quote_a)))
    kept = check(
        EM,
        one(
            "When viable monitoring exceeds an action limit, QA opens a deviation before product "
            "disposition.",
            (S_EM, quote_a),
        ),
    )

    notes = [a.message for a in dropped.advisories if a.code == "condition_not_reflected"]
    assert any("When viable monitoring exceeds an action limit" in note for note in notes)
    assert not [a for a in kept.advisories if a.code == "condition_not_reflected"]


def test_condition_paraphrase_is_not_noted() -> None:
    line = evidence("Who must sign the line clearance record before the run starts?")
    ref = ref_with(line, "both operations and QA")
    view = check(
        line,
        one(
            "Both operations and QA must sign the clearance record before the run can start.",
            (ref, "The run cannot start until both operations and QA sign the clearance record"),
        ),
    )

    assert view.advisories == []


def test_steps_out_of_source_order_are_noted() -> None:
    view = check(
        EM,
        answer(
            "answered",
            [
                block(
                    "step",
                    "Hold the room until QA documents the initial impact assessment.",
                    (S_EM, "on hold until QA documents the initial impact assessment"),
                ),
                block(
                    "step",
                    "When viable monitoring exceeds an action limit, QA opens a deviation.",
                    (S_EM, "When viable monitoring exceeds an action limit, QA opens a deviation"),
                ),
            ],
        ),
    )

    assert "order_differs_from_source" in [a.code for a in view.advisories]


def test_frequency_from_a_heading_is_noted() -> None:
    view = check(
        BALANCE,
        one(
            "The daily check uses two traceable weights before use.",
            (S_BAL, "The analyst verifies the balance with two traceable weights before use"),
        ),
    )

    notes = [a.message for a in view.advisories if a.code == "qualifier_not_in_cited_text"]
    assert notes and "Daily check" in notes[0] and "not treated as evidence" in notes[0]
    assert not view.blocks[0].withheld


def test_verification_language_is_noted() -> None:
    view = check(
        EM,
        one(
            "This step is verified: QA opens a deviation.",
            (S_EM, "QA opens a deviation before product disposition"),
        ),
    )
    assert "verification_language" in [a.code for a in view.advisories]


def test_claimed_answer_with_nothing_shown_is_noted() -> None:
    view = check(BALANCE, one("The range is 0.1 mg.", (S_BAL, "outside the acceptance range")))
    assert "status_without_shown_statements" in [a.code for a in view.advisories]


def test_missing_information_drops_unknown_refs() -> None:
    view = check(
        BALANCE,
        answer(
            "not_stated",
            [],
            missing=[missing_item("The numeric range", "Not stated.", S_BAL, "S8")],
        ),
    )

    assert view.missing_information[0].related_refs == [S_BAL]
    assert "S8" in view.unknown_refs
