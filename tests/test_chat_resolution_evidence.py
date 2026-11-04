"""Turn resolution and the evidence boundary for the chat prototype.

History may resolve a reference, but evidence only ever comes from the maintained retrieval path
(unchanged gate) over admitted documents, re-verified per turn. These tests pin that boundary.
"""

from __future__ import annotations

import dataclasses
import json
import shutil
from pathlib import Path

import pytest
from chat_support import BALANCE_QUESTION, DEMO_CORPUS, EM_QUESTION, OBSOLETE_TRAP, binding_for

from biotech_rag_assistant.answer import build_extractive_answer
from biotech_rag_assistant.chat.engine import ChatEngine
from biotech_rag_assistant.chat.evidence import (
    CorpusBinding,
    EvidenceBoundaryError,
    HeldOutPointer,
    assemble_evidence,
    held_out_pointers,
)
from biotech_rag_assistant.chat.provider import UnconfiguredProvider
from biotech_rag_assistant.chat.resolution import ActiveTopic, ResolvedTurn, resolve_turn
from biotech_rag_assistant.chat.settings import ChatSettings
from biotech_rag_assistant.models import RETRIEVABLE_STATUSES
from biotech_rag_assistant.retrieval import RetrievalConfig, query_retriever

CONFIG = RetrievalConfig(top_k=3)
NL_SUITE = DEMO_CORPUS / "evaluation/natural-language-queries.json"


@pytest.fixture(scope="module")
def binding() -> CorpusBinding:
    return binding_for()


def resolve(
    binding: CorpusBinding,
    message: str,
    *,
    topic: ActiveTopic | None = None,
    new_topic: bool = False,
) -> ResolvedTurn:
    return resolve_turn(
        message,
        turn_index=2 if topic else 1,
        active_topic=topic,
        new_topic=new_topic,
        binding=binding,
        config=CONFIG,
    )


@pytest.fixture(scope="module")
def em_topic(binding: CorpusBinding) -> ActiveTopic:
    resolved = resolve(binding, EM_QUESTION)
    assert resolved.resolution.kind == "standalone"
    assert resolved.next_topic is not None
    return resolved.next_topic


def nl_cases(outcome: str) -> list[str]:
    suite = json.loads(NL_SUITE.read_text("utf-8"))
    return [case["question"] for case in suite["cases"] if case["expected_outcome"] == outcome]


# --- The maintained retrieval path is reused unchanged ---


def test_chat_uses_the_maintained_relevance_gate() -> None:
    engine = ChatEngine({}, UnconfiguredProvider(), ChatSettings())
    maintained = RetrievalConfig()

    assert engine.retrieval_config.score_floor == maintained.score_floor
    assert engine.retrieval_config.min_top_coverage == maintained.min_top_coverage == 0.6
    assert engine.retrieval_config.method == "bm25"


@pytest.mark.parametrize("question", nl_cases("answer"))
def test_plain_question_retrieves_exactly_what_answer_retrieves(
    binding: CorpusBinding, question: str
) -> None:
    resolved = resolve(binding, question)
    maintained = build_extractive_answer(
        question, query_retriever(binding.retriever, question, CONFIG)
    )

    assert resolved.resolution.retrieval_query == question
    assert resolved.resolution.removed_words == []
    chat_ids = [hit.chunk.chunk_id for _, hits in resolved.hit_sets for hit in hits]
    assert chat_ids == [record["chunk_id"] for record in maintained.retrieved_chunks]


@pytest.mark.parametrize(
    "question",
    [
        *nl_cases("refusal"),
        "Can you please summarize the company vacation policy as a checklist?",
        "Explain the quarterly sales revenue figures in plain English",
        "Tell me the weather forecast for tomorrow afternoon, briefly",
    ],
)
def test_off_topic_questions_are_still_refused_after_normalization(
    binding: CorpusBinding, question: str
) -> None:
    resolved = resolve(binding, question)

    assert resolved.resolution.kind == "not_found"
    assert resolved.hit_sets == []


def test_task_words_are_removed_only_when_absent_from_the_corpus(
    binding: CorpusBinding,
) -> None:
    question = "Can you summarize the line clearance procedure as a checklist?"
    assert query_retriever(binding.retriever, question, CONFIG) == []  # refused as typed

    resolved = resolve(binding, question)
    assert {"summarize", "checklist"} <= set(resolved.resolution.removed_words)
    assert all(word not in binding.vocabulary for word in resolved.resolution.removed_words)
    assert resolved.hit_sets[0][1][0].chunk.doc_id == "SOP-OPS-007"

    in_vocabulary = dataclasses.replace(binding, vocabulary=binding.vocabulary | {"summarize"})
    kept = resolve(in_vocabulary, question)
    assert "summarize" not in kept.resolution.removed_words


# --- Follow-ups, topic changes, corrections, ambiguity ---


@pytest.mark.parametrize(
    ("message", "kind"),
    [
        ("Who is responsible?", "follow_up"),
        ("Explain that step", "follow_up"),
        ("Turn the stated procedure into a checklist", "follow_up"),
        ("What about that?", "follow_up"),
        ("And who approves reopening the room?", "follow_up_with_new_terms"),
    ],
)
def test_follow_up_reuses_the_anchor_question(
    binding: CorpusBinding, em_topic: ActiveTopic, message: str, kind: str
) -> None:
    resolved = resolve(binding, message, topic=em_topic)
    resolution = resolved.resolution

    assert resolution.kind == kind
    assert resolution.anchor_turn == 1
    assert resolution.anchor_query == EM_QUESTION
    assert resolution.anchor_message == EM_QUESTION
    origins = [origin for origin, _ in resolved.hit_sets]
    assert origins[0] == "anchor:turn_1"
    anchor_ids = [hit.chunk.chunk_id for hit in resolved.hit_sets[0][1]]
    assert "SOP-QA-001_v1_0_chunk_002" in anchor_ids  # the passage with the procedure's conditions
    assert resolved.next_topic == em_topic


def test_topic_change_drops_the_anchor(binding: CorpusBinding, em_topic: ActiveTopic) -> None:
    resolved = resolve(binding, "Who must sign the line clearance record before the run starts?",
                       topic=em_topic)

    assert resolved.resolution.kind == "topic_change"
    assert [origin for origin, _ in resolved.hit_sets] == ["current_message"]
    assert resolved.next_topic is not None and resolved.next_topic.turn_index == 2


def test_correction_replaces_the_topic(binding: CorpusBinding, em_topic: ActiveTopic) -> None:
    resolved = resolve(binding, "No, I meant the purified water loop sampling", topic=em_topic)
    resolution = resolved.resolution

    assert resolution.kind == "correction"
    assert resolution.retrieval_query == "the purified water loop sampling"
    assert resolution.removed_words[:3] == ["no", "i", "meant"]
    assert [origin for origin, _ in resolved.hit_sets] == ["current_message"]
    assert resolved.hit_sets[0][1][0].chunk.doc_id == "SPEC-QC-006"
    assert resolved.next_topic is not None
    assert resolved.next_topic.query == "the purified water loop sampling"


def test_unmatched_correction_clears_the_topic(
    binding: CorpusBinding, em_topic: ActiveTopic
) -> None:
    resolved = resolve(binding, "No, I meant the vacation policy", topic=em_topic)

    assert resolved.resolution.kind == "clarification_needed"
    assert resolved.hit_sets == []
    assert resolved.next_topic is None


def test_short_reference_without_a_topic_asks_for_clarification(binding: CorpusBinding) -> None:
    resolved = resolve(binding, "Explain that step")

    assert resolved.resolution.kind == "clarification_needed"
    assert resolved.hit_sets == []


def test_long_message_with_a_pronoun_is_not_a_clarification(binding: CorpusBinding) -> None:
    resolved = resolve(
        binding, "I know SOP-QA-009 is obsolete, but what did it say about verbal QA approval?"
    )

    assert resolved.resolution.kind == "not_found"


def test_new_topic_request_ignores_the_anchor(
    binding: CorpusBinding, em_topic: ActiveTopic
) -> None:
    resolved = resolve(binding, "Who is responsible?", topic=em_topic, new_topic=True)

    assert resolved.resolution.kind == "not_found"
    assert resolved.resolution.anchor_turn is None
    assert resolved.resolution.new_topic_requested is True


def test_courtesy_needs_no_search(binding: CorpusBinding, em_topic: ActiveTopic) -> None:
    resolved = resolve(binding, "Thanks!", topic=em_topic)

    assert resolved.resolution.kind == "courtesy"
    assert resolved.resolution.attempts == []
    assert resolved.next_topic == em_topic


# --- Evidence assembly re-verifies admissibility and provenance ---


def evidence_for(binding: CorpusBinding, question: str, max_passages: int = 6) -> list:
    return assemble_evidence(resolve(binding, question).hit_sets, binding, max_passages)


def test_evidence_is_admitted_exact_and_ordered(binding: CorpusBinding) -> None:
    evidence = evidence_for(binding, EM_QUESTION)
    raw = {doc.metadata.doc_id: doc for doc in binding.corpus.documents}

    assert [passage.ref for passage in evidence] == [f"S{i}" for i in range(1, len(evidence) + 1)]
    for passage in evidence:
        document = raw[passage.doc_id]
        assert passage.status in RETRIEVABLE_STATUSES
        assert passage.source_hash == document.metadata.source_hash
        assert passage.text == document.raw_text[passage.char_start : passage.char_end]
        assert passage.version == document.metadata.version
    # Passages of one document stay together and in source order.
    seen: list[str] = []
    for passage in evidence:
        if not seen or seen[-1] != passage.doc_id:
            assert passage.doc_id not in seen
            seen.append(passage.doc_id)
    for doc_id in seen:
        offsets = [p.char_start for p in evidence if p.doc_id == doc_id]
        assert offsets == sorted(offsets)


def test_model_payload_never_includes_section_headings(binding: CorpusBinding) -> None:
    for question in (EM_QUESTION, BALANCE_QUESTION):
        for passage in evidence_for(binding, question):
            payload = json.dumps(passage.model_payload())
            assert "section" not in payload
            assert passage.section_heading not in passage.text
            assert passage.section_heading not in payload


def test_evidence_cap_is_enforced(binding: CorpusBinding) -> None:
    assert len(evidence_for(binding, EM_QUESTION, max_passages=2)) == 2


def test_held_out_chunk_fails_closed(binding: CorpusBinding) -> None:
    status_blind_hits = query_retriever(binding.status_blind, OBSOLETE_TRAP, CONFIG)
    assert status_blind_hits[0].chunk.status == "Obsolete"

    with pytest.raises(EvidenceBoundaryError):
        assemble_evidence([("current_message", status_blind_hits)], binding, 6)


@pytest.mark.parametrize(
    "tamper",
    [
        {"text": "QA may skip the deviation."},
        {"source_hash": "sha256:" + "0" * 64},
        {"char_start": 0},
    ],
)
def test_tampered_chunk_fails_closed(binding: CorpusBinding, tamper: dict) -> None:
    hits = query_retriever(binding.retriever, EM_QUESTION, CONFIG)
    forged = [hits[0].model_copy(update={"chunk": hits[0].chunk.model_copy(update=tamper)})]

    with pytest.raises(EvidenceBoundaryError):
        assemble_evidence([("current_message", forged)], binding, 6)


# --- Held-out pointers carry identity only ---


def test_status_blind_pointer_names_the_retired_document(binding: CorpusBinding) -> None:
    pointers = held_out_pointers(binding, message=OBSOLETE_TRAP, query=OBSOLETE_TRAP, config=CONFIG)

    assert [(p.doc_id, p.status, p.reasons) for p in pointers] == [
        ("SOP-QA-009", "Obsolete", ["status_blind_match"])
    ]
    assert "text" not in HeldOutPointer.model_fields
    assert "96 hours" not in json.dumps([p.model_dump() for p in pointers])


@pytest.mark.parametrize("mention", ["SOP-QA-009", "sop qa 009", "Sop-Qa-009"])
def test_named_retired_document_is_reported_by_identity(
    binding: CorpusBinding, mention: str
) -> None:
    pointers = held_out_pointers(
        binding, message=f"What did {mention} say?", query=None, config=CONFIG
    )

    assert [(p.doc_id, p.reasons) for p in pointers] == [("SOP-QA-009", ["named_in_message"])]


def test_admitted_documents_are_never_pointers(binding: CorpusBinding) -> None:
    assert held_out_pointers(binding, message="What does SOP-QA-001 say?", query=None,
                             config=CONFIG) == []


# --- Corpus snapshot identity ---


def test_snapshot_identity_is_stable_and_tracks_status(tmp_path: Path) -> None:
    first, second = binding_for(), binding_for()
    assert first.snapshot.snapshot_id == second.snapshot.snapshot_id
    assert first.snapshot.documents_retrievable == 8

    copy = tmp_path / "corpus"
    shutil.copytree(DEMO_CORPUS, copy)
    sidecar = copy / "metadata/SOP-QA-002-deviation-triage.yaml"
    sidecar.write_text(sidecar.read_text("utf-8").replace("status: Effective", "status: Approved"))
    changed = binding_for(copy)

    assert changed.snapshot.snapshot_id != first.snapshot.snapshot_id
    assert "restart" in first.snapshot.note
