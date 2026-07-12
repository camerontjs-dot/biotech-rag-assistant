from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.answer import REFUSAL_TEXT, build_extractive_answer
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"


def _answer(query: str):
    corpus = load_corpus(DEMO_CORPUS)
    hits = run_retrieval(corpus.documents, query, RetrievalConfig(top_k=2))
    return build_extractive_answer(query, hits)


def test_extractive_answer_copies_retrieved_spans_with_source_markers() -> None:
    answer = _answer("viable excursion affected product lots immediate containment")

    assert answer.outcome == "answer"
    assert answer.citation_validation.valid
    assert answer.citations[0].chunk_id == "SOP-QA-001_v1_0_chunk_002"
    assert "[source: 1] SOP-QA-001 v1.0, Immediate containment, lines 9-9" in (
        answer.answer_text
    )
    assert "When viable monitoring exceeds an action limit" in answer.answer_text


def test_extractive_answer_refuses_without_hits() -> None:
    answer = _answer("zzzz qqqq impossible-token")

    assert answer.outcome == "refusal"
    assert answer.answer_text == REFUSAL_TEXT
    assert answer.citations == []
    assert answer.retrieved_chunks == []
    assert answer.citation_validation.valid


def test_extractive_answer_keeps_non_retrievable_documents_out() -> None:
    answer = _answer("membrane filtration 96 verbal")

    assert answer.outcome == "refusal"
    assert "SOP-QA-009" not in answer.answer_text
    assert answer.retrieved_chunks == []
