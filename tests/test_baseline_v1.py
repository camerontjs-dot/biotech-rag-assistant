from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

import pytest

from biotech_rag_assistant.answer import build_extractive_answer
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.models import Corpus
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    build_retriever,
    coverage,
    index_text,
    query_retriever,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_DIR = ROOT / "baselines/v1"
PROBES = json.loads((BASELINE_DIR / "near-miss-probes.json").read_text(encoding="utf-8"))

# Characterization, not specification. These tests pin Baseline V1's behavior on questions whose
# fact the corpus does not state (plans/public-generative-rag-v2.md section 1.8). Four near-miss
# probes are answered with passages that lack the fact; the planned answer layer should report them
# as `not_stated` instead. When a later slice changes this behavior on purpose, update the probe
# file and the plan in the same change.


def _probes(kind: str) -> list[dict]:
    return [probe for probe in PROBES["probes"] if probe["kind"] == kind]


def _ids(probe: dict) -> str:
    return probe["probe_id"]


@pytest.fixture(scope="module")
def corpus() -> Corpus:
    return load_corpus(ROOT / PROBES["corpus_dir"])


@pytest.fixture(scope="module")
def retriever(corpus: Corpus) -> BM25Retriever:
    return build_retriever(corpus.documents)


def _gated_hits(retriever: BM25Retriever, question: str):
    return query_retriever(retriever, question, RetrievalConfig(top_k=PROBES["top_k"]))


def test_probe_set_records_the_plan_findings() -> None:
    near_miss = _probes("near_miss")
    answered = [probe for probe in near_miss if probe["current_outcome"] == "answer"]
    best_control = max(probe["ungated_rank1_coverage"] for probe in _probes("supported_control"))

    assert len(near_miss) == 6
    assert len(answered) == 4
    assert sum(probe["ungated_rank1_coverage"] > best_control for probe in answered) == 3
    assert {probe["desired_disposition"] for probe in near_miss} == {"not_stated"}


@pytest.mark.parametrize("probe", PROBES["probes"], ids=_ids)
def test_probe_matches_recorded_baseline_behavior(probe: dict, retriever: BM25Retriever) -> None:
    question = probe["question"]
    hits = _gated_hits(retriever, question)
    assert build_extractive_answer(question, hits).outcome == probe["current_outcome"]

    ungated = retriever.query(question, top_k=1)
    assert ungated[0].chunk.chunk_id == probe["ungated_rank1_chunk_id"]
    rank1_coverage = coverage(question, index_text(ungated[0].chunk))
    assert round(rank1_coverage, PROBES["coverage_decimals"]) == probe["ungated_rank1_coverage"]
    if hits:
        # The relevance gate filters results; it never reorders them.
        assert hits[0].chunk.chunk_id == probe["ungated_rank1_chunk_id"]


@pytest.mark.parametrize("probe", _probes("near_miss"), ids=_ids)
def test_near_miss_fact_is_absent_from_the_topic_and_every_shown_passage(
    probe: dict, retriever: BM25Retriever
) -> None:
    fact = re.compile(probe["fact_pattern"])
    chunks_by_id = {chunk.chunk_id: chunk for chunk in retriever.chunks}

    assert not fact.search(chunks_by_id[probe["topic_chunk_id"]].text)
    for hit in _gated_hits(retriever, probe["question"]):
        assert not fact.search(hit.chunk.text), hit.chunk.chunk_id


@pytest.mark.parametrize("probe", _probes("supported_control"), ids=_ids)
def test_supported_control_answer_passage_states_the_fact(
    probe: dict, retriever: BM25Retriever
) -> None:
    hits = _gated_hits(retriever, probe["question"])
    assert re.search(probe["answer_pattern"], hits[0].chunk.text)


@pytest.mark.parametrize("probe", _probes("stale_trap"), ids=_ids)
def test_stale_trap_fact_exists_only_in_the_excluded_source(
    probe: dict, corpus: Corpus, retriever: BM25Retriever
) -> None:
    fact = re.compile(probe["fact_pattern"])
    sources = [
        document
        for document in corpus.documents
        if document.metadata.doc_id == probe["excluded_source_doc_id"]
    ]

    assert len(sources) == 1
    assert not sources[0].is_retrievable
    assert fact.search(sources[0].raw_text)
    assert not any(fact.search(chunk.text) for chunk in retriever.chunks)


def test_v1_corpus_matches_the_recorded_baseline() -> None:
    # The plan keeps the v1 corpus frozen as a regression fixture. Any edit to its documents,
    # sidecars, or chunk boundaries must come with a new baseline, not a silent drift.
    spec = importlib.util.spec_from_file_location(
        "record_baseline", ROOT / "scripts/record_baseline.py"
    )
    assert spec is not None and spec.loader is not None
    recorder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recorder)
    recorded = json.loads((BASELINE_DIR / "baseline.json").read_text(encoding="utf-8"))

    assert recorder.corpus_record(ROOT / recorded["corpus"]["dir"]) == recorded["corpus"]


def test_no_retrievable_v1_chunk_states_a_number(retriever: BM25Retriever) -> None:
    # Every quantity question against the v1 corpus is a near-miss or a refusal by construction.
    # Corpus v2 (plan Appendix A) adds explicit quantities.
    assert not [chunk.chunk_id for chunk in retriever.chunks if re.search(r"\d", chunk.text)]
