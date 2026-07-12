from __future__ import annotations

import json
from pathlib import Path

from biotech_rag_assistant.citations import (
    load_answer_fixture,
    load_retrieved_results,
    validate_answer_citations,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/citation-validation"


def _validate(retrieval_name: str, answer_name: str):
    return validate_answer_citations(
        load_retrieved_results(FIXTURES / retrieval_name),
        load_answer_fixture(FIXTURES / answer_name),
    )


def test_valid_citation_resolves_to_retrieved_chunk() -> None:
    result = _validate("retrieval-valid.json", "answer-valid.json")

    assert result.valid
    assert result.metric_name == "citation_resolves_to_retrieved_chunk"
    assert result.citation_resolves_to_retrieved_chunk
    assert result.resolved_citation_count == 1
    assert result.issues == []


def test_missing_answer_citation_fails_resolution_metric() -> None:
    result = _validate("retrieval-valid.json", "answer-missing-citation.json")

    assert not result.valid
    assert not result.citation_resolves_to_retrieved_chunk
    assert [issue.code for issue in result.issues] == ["missing_answer_citation"]


def test_hallucinated_chunk_id_fails_resolution() -> None:
    result = _validate("retrieval-valid.json", "answer-hallucinated-citation.json")

    assert not result.valid
    assert not result.citation_resolves_to_retrieved_chunk
    assert [issue.code for issue in result.issues] == ["unresolved_citation"]
    assert result.issues[0].chunk_id == "NOT-A-REAL-CHUNK"


def test_stale_retrieved_chunk_and_citation_hard_fail() -> None:
    result = _validate("retrieval-stale-leak.json", "answer-stale-citation.json")

    assert not result.valid
    assert result.citation_resolves_to_retrieved_chunk
    assert {issue.code for issue in result.issues} == {
        "stale_retrieved_chunk",
        "stale_citation",
    }


def test_refusal_without_citation_passes() -> None:
    result = _validate("retrieval-empty.json", "answer-refusal-valid.json")

    assert result.valid
    assert result.expected_outcome == "refusal"
    assert result.answer_citation_count == 0


def test_refusal_with_citation_fails() -> None:
    result = _validate("retrieval-valid.json", "answer-refusal-with-citation.json")

    assert not result.valid
    assert result.citation_resolves_to_retrieved_chunk
    assert [issue.code for issue in result.issues] == ["refusal_has_citation"]


def test_cli_record_includes_valid_flag() -> None:
    result = _validate("retrieval-valid.json", "answer-valid.json")

    payload = result.to_cli_record()

    assert json.dumps(payload)
    assert payload["valid"] is True
