"""Status-gate ablation: what the gate prevents, and what still catches a stale answer without it.

The demo's obsolete-document trap asks a question that only a retired SOP answers. These tests pin
the facts the demo's refusal explanation (ADR-018) relies on. With the status gate (ADR-005), the
question is refused. Without it, the same query path answers from the retired SOP, because the
relevance gate (ADR-012) measures topic match and the stale passage matches best. Answer assembly
then rejects that answer anyway, because citation validation checks status on its own (ADR-007).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from biotech_rag_assistant.answer import AnswerAssemblyError, build_extractive_answer
from biotech_rag_assistant.citations import (
    AnswerCitation,
    AnswerFixture,
    RetrievedChunkRecord,
    RetrievedResultsPayload,
    validate_answer_citations,
)
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.models import SourceDocument
from biotech_rag_assistant.retrieval import (
    RetrievalConfig,
    build_retriever,
    build_status_blind_retriever,
    coverage,
    held_out_hits,
    index_text,
    query_retriever,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
CONFIG = RetrievalConfig(top_k=3)

OBSOLETE_TRAP = "What is the membrane filtration hold time for sterility?"
DRAFT_TRAP = "Is a visual-only residue check acceptable at campaign changeover?"
TRAPS = [(OBSOLETE_TRAP, "SOP-QA-009", "Obsolete"), (DRAFT_TRAP, "SOP-QA-010", "Draft")]


@pytest.fixture(scope="module")
def documents() -> list[SourceDocument]:
    return load_corpus(DEMO_CORPUS).documents


@pytest.mark.parametrize(("question", "held_out_doc", "status"), TRAPS)
def test_status_gate_refuses_the_trap(
    documents: list[SourceDocument], question: str, held_out_doc: str, status: str
) -> None:
    assert query_retriever(build_retriever(documents), question, CONFIG) == []


@pytest.mark.parametrize(("question", "held_out_doc", "status"), TRAPS)
def test_relevance_gate_alone_would_answer_from_the_held_out_document(
    documents: list[SourceDocument], question: str, held_out_doc: str, status: str
) -> None:
    hits = query_retriever(build_status_blind_retriever(documents), question, CONFIG)

    assert hits, "without the status gate, the same query path answers"
    top = hits[0].chunk
    assert (top.doc_id, top.status) == (held_out_doc, status)
    assert coverage(question, index_text(top)) >= CONFIG.min_top_coverage


def test_answer_assembly_rejects_a_status_blind_answer(documents: list[SourceDocument]) -> None:
    hits = query_retriever(build_status_blind_retriever(documents), OBSOLETE_TRAP, CONFIG)

    with pytest.raises(AnswerAssemblyError):
        build_extractive_answer(OBSOLETE_TRAP, hits)

    result = validate_answer_citations(
        RetrievedResultsPayload(
            query=OBSOLETE_TRAP,
            hits=[RetrievedChunkRecord.model_validate(hit.to_cli_record()) for hit in hits],
        ),
        AnswerFixture(
            answer_text="status-blind extractive answer",
            citations=[
                AnswerCitation(chunk_id=hit.chunk.chunk_id, label=str(index))
                for index, hit in enumerate(hits, start=1)
            ],
            expected_outcome="answer",
        ),
    )
    assert {"stale_retrieved_chunk", "stale_citation"} <= {issue.code for issue in result.issues}


def test_held_out_hits_name_what_the_gate_kept_out(documents: list[SourceDocument]) -> None:
    hits = held_out_hits(build_status_blind_retriever(documents), OBSOLETE_TRAP, CONFIG)

    assert [(hit.rank, hit.chunk.chunk_id) for hit in hits] == [(1, "SOP-QA-009_v0_8_chunk_001")]
    assert "96 hours with verbal QA approval" in hits[0].chunk.text


@pytest.mark.parametrize(
    "question",
    [
        "What is the company vacation policy and paid days off?",
        # Terms from both held-out documents: no single passage clears the relevance gate.
        "membrane filtration verbal visual residue campaign changeover",
    ],
)
def test_held_out_hits_are_empty_when_the_gate_changed_nothing(
    documents: list[SourceDocument], question: str
) -> None:
    status_blind = build_status_blind_retriever(documents)

    assert query_retriever(status_blind, question, CONFIG) == []
    assert held_out_hits(status_blind, question, CONFIG) == []
