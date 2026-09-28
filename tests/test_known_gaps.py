"""Known gap: near-miss questions pass the relevance gate. Documented, not desired.

A near-miss question covers a topic the corpus discusses but asks for a fact it never states.
"What is the acceptance range for the analytical balance daily check?" The balance procedure
names an acceptance range and never gives one. The question reuses the document's own words, so
it clears the ADR-012 coverage gate and the extractive answer shows the passage. Its citations
resolve (ADR-007), and the answer is not in them.

Today the failure is benign: the extractive answer copies passages and asserts nothing. With a
generator it becomes the likely fabrication path, an invented value cited to a real passage. No
retrieval threshold can close it, because relevance measures topic match and these questions
match their topic. The check belongs at the claim layer: an answer may only state a value its
quoted evidence states.

These tests pin current behavior so any change is deliberate. If one fails because the behavior
improved, update the case. Do not loosen the assertion.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    build_retriever,
    query_retriever,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
CONFIG = RetrievalConfig(top_k=3)
DIGIT = re.compile(r"[0-9]")

# (question, top document, phrase that names the concept without its value)
NEAR_MISS_ANSWERED = [
    (
        "What is the acceptance range for the analytical balance daily check?",
        "CAL-ENG-005",
        "outside the acceptance range",
    ),
    (
        "How long an absence from the suite triggers gowning requalification?",
        "TRN-QA-004",
        "a long absence",
    ),
    (
        "What is the defined use period for printed copies stamped by document control?",
        "POL-DOC-003",
        "a defined use period",
    ),
    (
        "What is the action limit for viable environmental monitoring?",
        "SOP-QA-001",
        "exceeds an action limit",
    ),
]

NEAR_MISS_REFUSED = [
    "How many days does QA have to close a deviation?",
    "What is the action limit value for purified water?",
]

# Controls: same shape of question, but the passage states the fact.
SUPPORTED = [
    ("How many traceable weights are used for the daily balance check?", "two traceable weights"),
    ("Who must sign the line clearance record before the run starts?", "both operations and QA"),
]


@pytest.fixture(scope="module")
def retriever() -> BM25Retriever:
    return build_retriever(load_corpus(DEMO_CORPUS).documents)


@pytest.mark.parametrize(("question", "top_doc", "concept"), NEAR_MISS_ANSWERED)
def test_near_miss_is_answered_with_passages_that_do_not_state_the_value(
    retriever: BM25Retriever, question: str, top_doc: str, concept: str
) -> None:
    hits = query_retriever(retriever, question, CONFIG)

    assert hits, "known gap: the question clears the relevance gate"
    assert hits[0].chunk.doc_id == top_doc
    assert any(concept in hit.chunk.text for hit in hits)
    assert not any(DIGIT.search(hit.chunk.text) for hit in hits)


@pytest.mark.parametrize("question", NEAR_MISS_REFUSED)
def test_near_miss_with_value_vocabulary_is_refused(
    retriever: BM25Retriever, question: str
) -> None:
    assert query_retriever(retriever, question, CONFIG) == []


@pytest.mark.parametrize(("question", "fact"), SUPPORTED)
def test_supported_control_passage_states_the_fact(
    retriever: BM25Retriever, question: str, fact: str
) -> None:
    hits = query_retriever(retriever, question, CONFIG)

    assert any(fact in hit.chunk.text for hit in hits)
