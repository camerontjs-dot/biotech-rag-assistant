from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest

from biotech_rag_assistant.models import DocumentChunk
from biotech_rag_assistant.retrieval import index_text

ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = ROOT / "experiments/semantic_vs_bm25.py"
CHUNKS_PATH = ROOT / "docs/corpus-data.json"
QUERIES_PATH = ROOT / "experiments/queries-labeled.json"
RESULTS_PATH = ROOT / "experiments/comparison-results.json"

# The ADR-014 harness is a standalone script, not package code. ADR-016 changed chunk.text to the
# body-only cited span while the harness kept indexing chunk.text, so it stopped reproducing its own
# recorded inputs without any test noticing. These tests pin it to what production indexes and to
# the BM25 values recorded in comparison-results.json. The semantic arm needs the embedding model
# and is not exercised here.


@pytest.fixture(scope="module")
def harness() -> ModuleType:
    spec = importlib.util.spec_from_file_location("semantic_vs_bm25", HARNESS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def chunks() -> list[dict]:
    return json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))["chunks"]


def test_harness_indexes_the_same_text_as_production(
    harness: ModuleType, chunks: list[dict]
) -> None:
    for chunk in chunks:
        assert harness.index_text(chunk) == index_text(DocumentChunk.model_validate(chunk))


def test_harness_bm25_arm_reproduces_recorded_adr014_results(
    harness: ModuleType, chunks: list[dict]
) -> None:
    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))["queries"]
    recorded = {
        row["id"]: row
        for row in json.loads(RESULTS_PATH.read_text(encoding="utf-8"))["per_query"]
    }
    texts = [harness.index_text(chunk) for chunk in chunks]
    bm25 = harness.BM25Okapi([harness.tokenize(text) for text in texts])

    assert len(queries) == len(recorded) == 22
    for query in queries:
        scores = bm25.scores(harness.tokenize(query["query"]))
        order = harness.ranking(scores, chunks)
        row = recorded[query["id"]]
        assert harness.first_relevant_rank(order, chunks, query["relevant_doc"]) == (
            row["ranks"]["bm25"]
        ), query["id"]
        assert chunks[order[0]]["doc_id"] == row["top"]["bm25"]["doc"], query["id"]
        assert scores[order[0]] == pytest.approx(row["top"]["bm25"]["score"], rel=1e-9)
        assert harness.coverage(query["query"], texts[order[0]]) == pytest.approx(
            row["bm25_top_coverage"], rel=1e-9
        ), query["id"]
