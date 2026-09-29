from __future__ import annotations

from pathlib import Path

from biotech_rag_assistant.chunking import chunk_document
from biotech_rag_assistant.evidence import (
    authority_class,
    build_evidence_packet,
    classify_section_role,
    corpus_identity,
)
from biotech_rag_assistant.models import (
    Corpus,
    DocumentMetadata,
    IngestReport,
    RetrievalHit,
    SourceDocument,
)
from biotech_rag_assistant.retrieval import RetrievalConfig

SOURCE_HASH = "sha256:" + ("a" * 64)
RAW_TEXT = (
    "# Demo SOP\n"
    "\n"
    "## Procedure\n"
    "\n"
    "Alpha requirement is 10 units.\n"
    "\n"
    "Beta context stays here.\n"
)


def make_document(root: str = "/first") -> SourceDocument:
    metadata = DocumentMetadata(
        doc_id="SOP-DEMO-001",
        doc_title="Demo SOP",
        doc_type="SOP",
        version="1.0",
        status="Effective",
        effective_date="2026-01-01",
        department="QA",
        source_file_path=Path("documents/SOP-DEMO-001.md"),
        source_hash=SOURCE_HASH,
    )
    return SourceDocument(
        metadata_path=Path(root) / "metadata/SOP-DEMO-001.yaml",
        content_path=Path(root) / "documents/SOP-DEMO-001.md",
        raw_text=RAW_TEXT,
        computed_source_hash=SOURCE_HASH,
        metadata=metadata,
    )


def make_corpus(root: str = "/first") -> Corpus:
    document = make_document(root)
    return Corpus(
        corpus_dir=Path(root),
        documents=[document],
        report=IngestReport(
            corpus_dir=Path(root),
            metadata_files_seen=1,
            documents_valid=1,
            documents_retrievable=1,
            documents_excluded=0,
            issues=[],
        ),
    )


def make_hits(score: float = 5.5) -> tuple[SourceDocument, list[RetrievalHit]]:
    document = make_document()
    chunks = chunk_document(document)
    return document, [
        RetrievalHit(rank=1, score=score, chunk=chunks[0]),
        RetrievalHit(rank=2, score=2.0, chunk=chunks[1]),
    ]


def test_packet_identity_is_pinned_and_scores_are_not_identity_bearing() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    config = RetrievalConfig(top_k=1)
    packet = build_evidence_packet(
        corpus=corpus,
        query="  What   is ALPHA? ",
        hits=hits[:1],
        config=config,
    )

    assert packet.query_id == (
        "q1:4639f9d5cf332709b64e2fb40bb729b1d817c8303a2a10a6b4a2eb60b84535b2"
    )
    assert packet.corpus_identity == (
        "corpus1:bc38502105d515f3165811b6384e92d1b7648923a8263b6193b91985e3b2b77e"
    )
    assert packet.retrieval_config_id == (
        "rc1:7fbb998312e8f167803b5739856754b529f43a2ceb96ccc0311dd0fd4c7ea6cf"
    )
    assert packet.packet_identity == (
        "ep1:e9f1ee607e28f89b070473d554f6742f4d9fbbc00dd934a1664539cdee80e8f3"
    )

    _document, rescored_hits = make_hits(score=999.0)
    rescored = build_evidence_packet(
        corpus=corpus,
        query="  What   is ALPHA? ",
        hits=rescored_hits[:1],
        config=config,
    )
    assert rescored.packet_identity == packet.packet_identity
    assert (
        rescored.admitted[0].nomination.raw_score
        != packet.admitted[0].nomination.raw_score
    )


def test_corpus_identity_ignores_local_filesystem_root() -> None:
    assert corpus_identity(make_corpus("/one/worktree")) == corpus_identity(
        make_corpus("/another/clone")
    )


def test_query_config_budget_and_exclusions_are_identity_bearing() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    base = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=hits[:1],
        config=RetrievalConfig(top_k=1),
    )
    different_query = build_evidence_packet(
        corpus=corpus,
        query="What is beta?",
        hits=hits[:1],
        config=RetrievalConfig(top_k=1),
    )
    different_config = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=hits,
        config=RetrievalConfig(top_k=2),
    )
    different_budget = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=hits[:1],
        config=RetrievalConfig(top_k=1),
        max_tokens=100,
    )
    duplicate = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=[
            hits[0],
            RetrievalHit(rank=2, score=1.0, chunk=hits[0].chunk),
        ],
        config=RetrievalConfig(top_k=2),
    )

    assert different_query.packet_identity != base.packet_identity
    assert different_config.packet_identity != base.packet_identity
    assert different_budget.packet_identity != base.packet_identity
    assert duplicate.packet_identity != base.packet_identity
    assert duplicate.excluded_candidate_summary == {"duplicate_source_span": 1}


def test_source_identity_and_admitted_order_are_identity_bearing() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    config = RetrievalConfig(top_k=2)
    normal = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=hits,
        config=config,
    )
    reversed_order = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=list(reversed(hits)),
        config=config,
    )

    changed_chunk = hits[0].chunk.model_copy(
        update={"source_hash": "sha256:" + ("b" * 64)}
    )
    changed_source = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=[RetrievalHit(rank=1, score=hits[0].score, chunk=changed_chunk)],
        config=RetrievalConfig(top_k=1),
    )
    original_one = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=hits[:1],
        config=RetrievalConfig(top_k=1),
    )

    assert reversed_order.packet_identity != normal.packet_identity
    assert changed_source.packet_identity != original_one.packet_identity


def test_non_retrievable_nomination_fails_closed_at_packet_admission() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    stale_chunk = hits[0].chunk.model_copy(update={"status": "Obsolete"})
    packet = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=[RetrievalHit(rank=1, score=5.5, chunk=stale_chunk)],
        config=RetrievalConfig(top_k=1),
    )

    assert packet.admitted == []
    assert packet.excluded_candidate_summary == {"non_retrievable_status": 1}


def test_token_budget_exclusion_is_deterministic() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    config = RetrievalConfig(top_k=2)

    first = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=hits,
        config=config,
        max_tokens=6,
    )
    second = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=hits,
        config=config,
        max_tokens=6,
    )

    assert first.packet_identity == second.packet_identity
    assert first.evidence_budget.used_items == 1
    assert first.evidence_budget.used_tokens == 6
    assert first.excluded_candidate_summary == {"evidence_token_budget": 1}


def test_same_section_expansion_is_explicit_and_off_by_default() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    config = RetrievalConfig(top_k=1)

    default = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=hits[:1],
        config=config,
        max_items=2,
    )
    expanded = build_evidence_packet(
        corpus=corpus,
        query="What is alpha?",
        hits=hits[:1],
        config=config,
        max_items=2,
        expand_section=True,
    )

    assert len(default.admitted) == 1
    assert len(expanded.admitted) == 2
    expansion = expanded.admitted[1]
    assert expansion.admission_reason == "same_section_expansion"
    assert expansion.nomination.nomination_kind == "section_expansion"
    assert expansion.nomination.parent_context_id == (
        expanded.admitted[0].nomination.nomination_id
    )
    assert expanded.excluded_candidate_summary == {"duplicate_source_span": 1}
    assert expanded.packet_identity != default.packet_identity


def test_retrieval_hits_consume_budget_before_section_expansion() -> None:
    corpus = make_corpus()
    _document, hits = make_hits()
    packet = build_evidence_packet(
        corpus=corpus,
        query="What does the procedure say?",
        hits=hits,
        config=RetrievalConfig(top_k=2),
        max_items=2,
        expand_section=True,
    )

    assert [item.nomination.nomination_kind for item in packet.admitted] == [
        "chunk",
        "chunk",
    ]
    assert [item.nomination.chunk_id for item in packet.admitted] == [
        hits[0].chunk.chunk_id,
        hits[1].chunk.chunk_id,
    ]


def test_authority_and_section_roles_are_descriptive_mechanics() -> None:
    assert authority_class("Policy") == "controlled_policy"
    assert authority_class("SOP") == "controlled_procedure"
    assert authority_class("Specification") == "controlled_specification"
    assert authority_class("TrainingNote") == "training_aid"
    assert classify_section_role("Revision History") == "revision_history"
    assert classify_section_role("References") == "references"
    assert classify_section_role("Definitions") == "definitions"
    assert classify_section_role("Responsibilities") == "responsibilities"
    assert classify_section_role("Procedure") == "normative"
