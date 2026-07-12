from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    coverage,
    run_retrieval,
    tokenize,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"


def _retriever() -> BM25Retriever:
    corpus = load_corpus(DEMO_CORPUS)
    return BM25Retriever(chunk_documents(corpus.documents))


def test_tokenizer_is_lowercase_and_deterministic() -> None:
    assert tokenize("QA Batch-Release, 21 CFR!") == ["qa", "batch", "release", "21", "cfr"]
    assert tokenize("QA Batch-Release, 21 CFR!") == tokenize("qa batch release 21 cfr")


def test_known_query_returns_expected_top_chunk() -> None:
    hits = _retriever().query(
        "viable excursion affected product lots immediate containment",
        top_k=3,
    )

    assert hits
    assert hits[0].chunk.chunk_id == "SOP-QA-001_v1_0_chunk_002"
    assert hits[0].chunk.source_hash.startswith("sha256:")


def test_shared_retrieval_config_matches_bm25_baseline() -> None:
    corpus = load_corpus(DEMO_CORPUS)
    query = "viable excursion affected product lots immediate containment"

    direct_hits = BM25Retriever(chunk_documents(corpus.documents)).query(query, top_k=3)
    shared_hits = run_retrieval(corpus.documents, query, RetrievalConfig(top_k=3))

    assert [hit.chunk.chunk_id for hit in shared_hits] == [
        hit.chunk.chunk_id for hit in direct_hits
    ]


def test_bm25_ranking_is_deterministic() -> None:
    retriever = _retriever()

    first = retriever.query("document control current approved version", top_k=5)
    second = retriever.query("document control current approved version", top_k=5)

    assert [(hit.chunk.chunk_id, hit.score) for hit in first] == [
        (hit.chunk.chunk_id, hit.score) for hit in second
    ]


def test_unsupported_query_returns_no_hits() -> None:
    hits = _retriever().query("zzzz qqqq impossible-token", top_k=5)

    assert hits == []


def test_obsolete_only_terms_are_not_retrieved() -> None:
    hits = _retriever().query("membrane filtration 96 verbal", top_k=5)

    assert hits == []


def test_coverage_counts_distinctive_terms_only() -> None:
    # Stopwords are ignored; coverage is the fraction of content terms present.
    assert coverage("the deviation and the record", "deviation triage record") == 1.0
    assert coverage("vacation policy benefits", "deviation triage record") == 0.0


def test_offtopic_question_refuses_via_coverage_gate() -> None:
    # An out-of-domain question shares only incidental tokens with the corpus; the
    # relevance gate (ADR-012) refuses it rather than copying a loosely related passage.
    documents = load_corpus(DEMO_CORPUS).documents
    hits = run_retrieval(
        documents,
        "What is the company vacation policy and paid days off?",
        RetrievalConfig(top_k=5),
    )

    assert hits == []


def test_relevant_question_passes_coverage_gate() -> None:
    documents = load_corpus(DEMO_CORPUS).documents
    hits = run_retrieval(
        documents,
        "viable excursion affected product lots immediate containment",
        RetrievalConfig(top_k=3),
    )

    assert hits
    assert hits[0].chunk.doc_id == "SOP-QA-001"


def test_coverage_gate_is_policy_not_baked_into_bm25() -> None:
    # The low-level retriever stays pure BM25 (gate off by default); the relevance gate
    # is applied as policy through RetrievalConfig.min_top_coverage.
    retriever = _retriever()
    question = "What is the company vacation policy and paid days off?"

    assert retriever.query(question, top_k=5)  # ungated BM25 finds incidental overlap
    assert retriever.query(question, top_k=5, min_top_coverage=0.6) == []  # gated: refuses
