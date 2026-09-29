from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import (
    EvidenceBudget,
    build_evidence_packet,
    corpus_identity,
    make_query_id,
    normalize_query,
    retrieval_config_id,
)
from biotech_rag_assistant.models import RetrievalHit
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
QUERY = "viable excursion affected product lots immediate containment"


def packet(
    *,
    top_k: int = 3,
    budget: EvidenceBudget | None = None,
):
    corpus = load_corpus(DEMO_CORPUS)
    config = RetrievalConfig(top_k=top_k)
    hits = run_retrieval(corpus.documents, QUERY, config)
    return build_evidence_packet(
        corpus,
        QUERY,
        hits,
        config,
        budget=budget,
    )


def test_query_and_config_ids_are_stable() -> None:
    assert normalize_query("  viable   excursion\n affected  ") == (
        "viable excursion affected"
    )
    assert make_query_id("viable excursion affected") == make_query_id(
        "  viable   excursion affected "
    )
    config = RetrievalConfig(top_k=3)
    assert retrieval_config_id(config) == retrieval_config_id(
        RetrievalConfig(top_k=3)
    )


def test_legacy_corpus_gets_explicit_derived_identity() -> None:
    corpus = load_corpus(DEMO_CORPUS)
    first = corpus_identity(corpus)
    second = corpus_identity(corpus)

    assert first.startswith("cm1:derived:")
    assert first == second


def test_identical_inputs_produce_identical_packet_identity() -> None:
    first = packet()
    second = packet()

    assert first.packet_id.startswith("ep1:")
    assert first.packet_id == second.packet_id
    assert first.query_id == second.query_id
    assert first.admitted_nominations
    assert first.diagnostics["scores_excluded_from_identity"] is True


def test_raw_score_changes_do_not_change_packet_identity() -> None:
    corpus = load_corpus(DEMO_CORPUS)
    config = RetrievalConfig(top_k=3)
    hits = run_retrieval(corpus.documents, QUERY, config)
    altered = [
        RetrievalHit(rank=hit.rank, score=hit.score + 1000.0, chunk=hit.chunk)
        for hit in hits
    ]

    original = build_evidence_packet(corpus, QUERY, hits, config)
    changed_scores = build_evidence_packet(corpus, QUERY, altered, config)

    assert original.packet_id == changed_scores.packet_id
    assert (
        original.admitted_nominations[0].raw_score
        != changed_scores.admitted_nominations[0].raw_score
    )


def test_admitted_source_identity_change_changes_packet_identity() -> None:
    corpus = load_corpus(DEMO_CORPUS)
    config = RetrievalConfig(top_k=3)
    hits = run_retrieval(corpus.documents, QUERY, config)
    first = build_evidence_packet(corpus, QUERY, hits, config)
    second = build_evidence_packet(corpus, QUERY, hits[1:], config)

    assert first.packet_id != second.packet_id
    assert first.admitted_nominations[0].chunk_id != second.admitted_nominations[0].chunk_id


def test_item_budget_is_mechanical_and_recorded() -> None:
    result = packet(
        top_k=5,
        budget=EvidenceBudget(max_items=1, max_context_chars=12_000),
    )

    assert len(result.admitted_nominations) == 1
    assert result.exclusion_summary["item_budget_exhausted"] >= 1


def test_context_budget_can_exclude_without_reordering() -> None:
    unrestricted = packet(top_k=3)
    first_chars = len(unrestricted.admitted_nominations[0].text)
    limited = packet(
        top_k=3,
        budget=EvidenceBudget(
            max_items=3,
            max_context_chars=first_chars,
        ),
    )

    assert limited.admitted_nominations[0].chunk_id == (
        unrestricted.admitted_nominations[0].chunk_id
    )
    assert len(limited.admitted_nominations) == 1
    assert limited.exclusion_summary["context_budget_exhausted"] >= 1


def test_section_expansion_is_explicit_and_preserves_parent_provenance() -> None:
    baseline = packet(
        top_k=1,
        budget=EvidenceBudget(max_items=10, max_context_chars=50_000),
    )
    expanded = packet(
        top_k=1,
        budget=EvidenceBudget(
            max_items=10,
            max_context_chars=50_000,
            expand_sections=True,
        ),
    )

    assert baseline.admitted_nominations[0].nomination_kind == "chunk"
    expansions = [
        item
        for item in expanded.admitted_nominations
        if item.nomination_kind == "section_expansion"
    ]
    if expansions:
        assert all(
            item.parent_context_id
            == expanded.admitted_nominations[0].nomination_id
            for item in expansions
        )
        assert all(item.representation_level == "section" for item in expansions)


def test_packet_schema_has_no_generated_content_fields() -> None:
    result = packet()
    payload = result.to_record()

    forbidden = {
        "answer",
        "answer_text",
        "generated_text",
        "completion",
        "claims",
    }
    assert forbidden.isdisjoint(payload)
    assert all(forbidden.isdisjoint(item) for item in payload["admitted_nominations"])


def test_only_retrievable_statuses_are_admitted() -> None:
    result = packet(top_k=20)
    assert result.admitted_nominations
    assert {
        item.status for item in result.admitted_nominations
    } <= {"Approved", "Effective"}
