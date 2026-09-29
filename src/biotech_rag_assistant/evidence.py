"""Deterministic retrieval nominations and EvidencePacket v1 assembly."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.models import (
    RETRIEVABLE_STATUSES,
    Corpus,
    DocumentChunk,
    DocumentStatus,
    RetrievalHit,
)
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    query_retriever,
)

PACKET_SCHEMA_VERSION = "1"
TOKEN_ESTIMATE_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WHITESPACE_RE = re.compile(r"\s+")

NominationKind = Literal["chunk", "section_expansion", "cross_reference_admission"]
RepresentationLevel = Literal["chunk", "section", "document"]
SectionRole = Literal[
    "normative",
    "definitions",
    "responsibilities",
    "references",
    "revision_history",
]

AUTHORITY_CLASS_BY_DOC_TYPE = {
    "Policy": "controlled_policy",
    "SOP": "controlled_procedure",
    "Specification": "controlled_specification",
    "CalibrationNote": "technical_record",
    "TechnicalNote": "technical_record",
    "TrainingNote": "training_aid",
    "DeviationExample": "worked_example",
}


class RetrievalReason(BaseModel):
    """One inspectable retrieval signal that nominated an item."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    signal: str = Field(min_length=1)
    rank: int = Field(ge=1)
    raw_score: float


class RetrievalNomination(BaseModel):
    """Typed nomination that preserves source identity and retrieval provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nomination_id: str = Field(pattern=r"^nom1:[a-f0-9]{64}$")
    query_id: str = Field(pattern=r"^q1:[a-f0-9]{64}$")
    chunk_id: str = Field(min_length=1)
    doc_id: str = Field(min_length=1)
    doc_title: str = Field(min_length=1)
    doc_type: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: DocumentStatus
    source_file_path: str = Field(min_length=1)
    source_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    section_heading: str = Field(min_length=1)
    text: str = Field(min_length=1)
    retrieval_signal: str = Field(min_length=1)
    raw_score: float
    rank: int = Field(ge=1)
    retrieval_config_id: str = Field(pattern=r"^rc1:[a-f0-9]{64}$")
    corpus_identity: str = Field(pattern=r"^[a-z][a-z0-9_-]*:[a-f0-9]{64}$")
    parent_context_id: str | None = None
    authorization_scope: str | None = None
    nomination_kind: NominationKind
    retrieval_reasons: list[RetrievalReason]
    representation_level: RepresentationLevel
    section_role: SectionRole
    authority_class: str = Field(min_length=1)
    token_estimate: int = Field(ge=1)
    expansion_handle: str = Field(pattern=r"^section1:[a-f0-9]{64}$")


class AdmittedEvidence(BaseModel):
    """One nomination admitted to the packet, with mechanical provenance."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nomination: RetrievalNomination
    admission_reason: Literal["retrieval_rank", "same_section_expansion"]


class EvidenceBudget(BaseModel):
    """Configured and consumed evidence budget."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    max_items: int = Field(ge=1)
    max_tokens: int = Field(ge=1)
    used_items: int = Field(ge=0)
    used_tokens: int = Field(ge=0)


class PacketDiagnostics(BaseModel):
    """Diagnostics deliberately excluded from the packet identity."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    nomination_count: int = Field(ge=0)
    admitted_count: int = Field(ge=0)
    raw_scores: dict[str, float]
    ranks: dict[str, int]


class EvidencePacket(BaseModel):
    """Immutable evidence boundary assembled after mechanical admission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"] = PACKET_SCHEMA_VERSION
    query: str = Field(min_length=1)
    normalized_query: str = Field(min_length=1)
    query_id: str = Field(pattern=r"^q1:[a-f0-9]{64}$")
    corpus_identity: str = Field(pattern=r"^[a-z][a-z0-9_-]*:[a-f0-9]{64}$")
    retrieval_config_id: str = Field(pattern=r"^rc1:[a-f0-9]{64}$")
    aperture_id: str | None = None
    admitted: list[AdmittedEvidence]
    excluded_candidate_summary: dict[str, int]
    evidence_budget: EvidenceBudget
    diagnostics: PacketDiagnostics
    packet_identity: str = Field(pattern=r"^ep1:[a-f0-9]{64}$")

    def to_cli_record(self) -> dict[str, object]:
        """JSON-compatible record shared by CLI and API."""
        return self.model_dump(mode="json")


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _identity(prefix: str, value: object) -> str:
    return f"{prefix}:{hashlib.sha256(_canonical_json(value)).hexdigest()}"


def normalize_query(query: str) -> str:
    """Normalize query text for stable identity without changing displayed input."""
    normalized = unicodedata.normalize("NFC", query)
    normalized = WHITESPACE_RE.sub(" ", normalized.strip())
    return normalized.casefold()


def query_identity(query: str) -> str:
    """Stable identity for a normalized query."""
    normalized = normalize_query(query)
    return f"q1:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"


def retrieval_config_identity(config: RetrievalConfig) -> str:
    """Stable identity for the complete retrieval configuration."""
    return _identity("rc1", config.model_dump(mode="json"))


def corpus_identity(corpus: Corpus) -> str:
    """Portable identity over validated metadata and verified source hashes.

    The maintained v1 corpus has no manifest file. This canonical record serves the same
    change-detection role without including local filesystem roots.
    """
    records = []
    for document in corpus.documents:
        metadata = document.metadata
        records.append(
            {
                "doc_id": metadata.doc_id,
                "doc_type": metadata.doc_type,
                "version": metadata.version,
                "status": metadata.status,
                "effective_date": metadata.effective_date.isoformat(),
                "review_due_date": (
                    metadata.review_due_date.isoformat()
                    if metadata.review_due_date is not None
                    else None
                ),
                "department": metadata.department,
                "source_file_path": metadata.source_file_path.as_posix(),
                "source_hash": metadata.source_hash,
            }
        )
    records.sort(
        key=lambda row: (
            row["doc_id"],
            row["version"],
            row["status"],
            row["source_file_path"],
        )
    )
    return _identity("corpus1", records)


def estimate_tokens(text: str) -> int:
    """Deterministic provider-neutral token estimate used only for evidence budgets."""
    return max(1, len(TOKEN_ESTIMATE_RE.findall(text)))


def classify_section_role(section_heading: str) -> SectionRole:
    """Mechanically classify a heading; this is not semantic support assessment."""
    heading = section_heading.casefold()
    if "revision" in heading or "history" in heading:
        return "revision_history"
    if "reference" in heading:
        return "references"
    if "definition" in heading:
        return "definitions"
    if "responsibilit" in heading:
        return "responsibilities"
    return "normative"


def authority_class(doc_type: str) -> str:
    """Descriptive document class. Slice 4 does not use it as a trust score."""
    try:
        return AUTHORITY_CLASS_BY_DOC_TYPE[doc_type]
    except KeyError as exc:
        raise ValueError(f"unsupported doc_type for authority class: {doc_type}") from exc


def section_expansion_handle(chunk: DocumentChunk) -> str:
    """Stable handle for explicit same-section expansion."""
    return _identity(
        "section1",
        {
            "doc_id": chunk.doc_id,
            "version": chunk.version,
            "section_heading": chunk.section_heading,
        },
    )


def _nomination_id(
    *,
    query_id: str,
    corpus_id: str,
    config_id: str,
    chunk: DocumentChunk,
    nomination_kind: NominationKind,
    parent_context_id: str | None,
) -> str:
    return _identity(
        "nom1",
        {
            "query_id": query_id,
            "corpus_identity": corpus_id,
            "retrieval_config_id": config_id,
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "version": chunk.version,
            "source_hash": chunk.source_hash,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "nomination_kind": nomination_kind,
            "parent_context_id": parent_context_id,
        },
    )


def nomination_from_hit(
    hit: RetrievalHit,
    *,
    query_id: str,
    corpus_id: str,
    config_id: str,
) -> RetrievalNomination:
    """Project a maintained retrieval hit into the nomination contract."""
    chunk = hit.chunk
    nomination_kind: NominationKind = "chunk"
    return RetrievalNomination(
        nomination_id=_nomination_id(
            query_id=query_id,
            corpus_id=corpus_id,
            config_id=config_id,
            chunk=chunk,
            nomination_kind=nomination_kind,
            parent_context_id=None,
        ),
        query_id=query_id,
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        doc_title=chunk.doc_title,
        doc_type=chunk.doc_type,
        version=chunk.version,
        status=chunk.status,
        source_file_path=chunk.source_file_path.as_posix(),
        source_hash=chunk.source_hash,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        section_heading=chunk.section_heading,
        text=chunk.text,
        retrieval_signal="bm25",
        raw_score=hit.score,
        rank=hit.rank,
        retrieval_config_id=config_id,
        corpus_identity=corpus_id,
        parent_context_id=None,
        authorization_scope=None,
        nomination_kind=nomination_kind,
        retrieval_reasons=[
            RetrievalReason(
                signal="bm25",
                rank=hit.rank,
                raw_score=hit.score,
            )
        ],
        representation_level="chunk",
        section_role=classify_section_role(chunk.section_heading),
        authority_class=authority_class(chunk.doc_type),
        token_estimate=estimate_tokens(chunk.text),
        expansion_handle=section_expansion_handle(chunk),
    )


def _expansion_nomination(
    chunk: DocumentChunk,
    *,
    parent: RetrievalNomination,
) -> RetrievalNomination:
    nomination_kind: NominationKind = "section_expansion"
    return RetrievalNomination(
        nomination_id=_nomination_id(
            query_id=parent.query_id,
            corpus_id=parent.corpus_identity,
            config_id=parent.retrieval_config_id,
            chunk=chunk,
            nomination_kind=nomination_kind,
            parent_context_id=parent.nomination_id,
        ),
        query_id=parent.query_id,
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        doc_title=chunk.doc_title,
        doc_type=chunk.doc_type,
        version=chunk.version,
        status=chunk.status,
        source_file_path=chunk.source_file_path.as_posix(),
        source_hash=chunk.source_hash,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        section_heading=chunk.section_heading,
        text=chunk.text,
        retrieval_signal=parent.retrieval_signal,
        raw_score=parent.raw_score,
        rank=parent.rank,
        retrieval_config_id=parent.retrieval_config_id,
        corpus_identity=parent.corpus_identity,
        parent_context_id=parent.nomination_id,
        authorization_scope=parent.authorization_scope,
        nomination_kind=nomination_kind,
        retrieval_reasons=list(parent.retrieval_reasons),
        representation_level="chunk",
        section_role=classify_section_role(chunk.section_heading),
        authority_class=authority_class(chunk.doc_type),
        token_estimate=estimate_tokens(chunk.text),
        expansion_handle=section_expansion_handle(chunk),
    )


def _source_span_key(nomination: RetrievalNomination) -> tuple[str, int, int]:
    return (
        nomination.source_hash,
        nomination.char_start,
        nomination.char_end,
    )


def _packet_identity_payload(
    *,
    normalized_query: str,
    corpus_id: str,
    config_id: str,
    aperture_id: str | None,
    admitted: list[AdmittedEvidence],
    excluded_summary: dict[str, int],
    max_items: int,
    max_tokens: int,
) -> dict[str, object]:
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "normalized_query": normalized_query,
        "corpus_identity": corpus_id,
        "retrieval_config_id": config_id,
        "aperture_id": aperture_id,
        "admitted": [
            [
                item.nomination.chunk_id,
                item.nomination.doc_id,
                item.nomination.version,
                item.nomination.status,
                item.nomination.source_hash,
                item.nomination.char_start,
                item.nomination.char_end,
                item.nomination.nomination_kind,
            ]
            for item in admitted
        ],
        "excluded_candidate_summary": excluded_summary,
        "evidence_budget": {
            "max_items": max_items,
            "max_tokens": max_tokens,
        },
    }


def build_evidence_packet(
    *,
    corpus: Corpus,
    query: str,
    hits: list[RetrievalHit],
    config: RetrievalConfig,
    max_items: int | None = None,
    max_tokens: int = 2000,
    expand_section: bool = False,
    aperture_id: str | None = None,
) -> EvidencePacket:
    """Build an EvidencePacket from retrieval output using mechanical admission only."""
    if not query.strip():
        raise ValueError("query must not be blank")
    if max_tokens < 1:
        raise ValueError("max_tokens must be at least 1")

    item_limit = config.top_k if max_items is None else max_items
    if item_limit < 1:
        raise ValueError("max_items must be at least 1")

    normalized = normalize_query(query)
    qid = query_identity(query)
    cid = corpus_identity(corpus)
    config_id = retrieval_config_identity(config)

    excluded: dict[str, int] = defaultdict(int)
    admitted: list[AdmittedEvidence] = []
    seen_spans: set[tuple[str, int, int]] = set()
    used_tokens = 0
    nomination_count = 0
    raw_scores: dict[str, float] = {}
    ranks: dict[str, int] = {}

    def try_admit(
        nomination: RetrievalNomination,
        reason: Literal["retrieval_rank", "same_section_expansion"],
    ) -> bool:
        nonlocal used_tokens, nomination_count
        nomination_count += 1
        raw_scores[nomination.nomination_id] = nomination.raw_score
        ranks[nomination.nomination_id] = nomination.rank

        if nomination.status not in RETRIEVABLE_STATUSES:
            excluded["non_retrievable_status"] += 1
            return False

        key = _source_span_key(nomination)
        if key in seen_spans:
            excluded["duplicate_source_span"] += 1
            return False

        if len(admitted) >= item_limit:
            excluded["evidence_item_budget"] += 1
            return False

        if used_tokens + nomination.token_estimate > max_tokens:
            excluded["evidence_token_budget"] += 1
            return False

        admitted.append(
            AdmittedEvidence(
                nomination=nomination,
                admission_reason=reason,
            )
        )
        seen_spans.add(key)
        used_tokens += nomination.token_estimate
        return True

    all_chunks = chunk_documents(corpus.documents) if expand_section else []
    section_chunks: dict[tuple[str, str, str], list[DocumentChunk]] = defaultdict(list)
    if expand_section:
        for chunk in all_chunks:
            section_chunks[
                (chunk.doc_id, chunk.version, chunk.section_heading)
            ].append(chunk)
        for chunks in section_chunks.values():
            chunks.sort(key=lambda chunk: (chunk.chunk_index, chunk.chunk_id))

    parents_for_expansion: list[RetrievalNomination] = []
    for hit in hits:
        nomination = nomination_from_hit(
            hit,
            query_id=qid,
            corpus_id=cid,
            config_id=config_id,
        )
        if try_admit(nomination, "retrieval_rank") and expand_section:
            parents_for_expansion.append(nomination)

    # Retrieval nominations always consume budget before optional context expansion. Expansion
    # can enrich admitted evidence, but it cannot displace a lower-ranked retrieved hit.
    for parent in parents_for_expansion:
        key = (
            parent.doc_id,
            parent.version,
            parent.section_heading,
        )
        for chunk in section_chunks.get(key, []):
            expansion = _expansion_nomination(chunk, parent=parent)
            try_admit(expansion, "same_section_expansion")

    excluded_summary = dict(sorted(excluded.items()))
    budget = EvidenceBudget(
        max_items=item_limit,
        max_tokens=max_tokens,
        used_items=len(admitted),
        used_tokens=used_tokens,
    )
    identity_payload = _packet_identity_payload(
        normalized_query=normalized,
        corpus_id=cid,
        config_id=config_id,
        aperture_id=aperture_id,
        admitted=admitted,
        excluded_summary=excluded_summary,
        max_items=item_limit,
        max_tokens=max_tokens,
    )
    packet_id = _identity("ep1", identity_payload)

    return EvidencePacket(
        query=query,
        normalized_query=normalized,
        query_id=qid,
        corpus_identity=cid,
        retrieval_config_id=config_id,
        aperture_id=aperture_id,
        admitted=admitted,
        excluded_candidate_summary=excluded_summary,
        evidence_budget=budget,
        diagnostics=PacketDiagnostics(
            nomination_count=nomination_count,
            admitted_count=len(admitted),
            raw_scores=raw_scores,
            ranks=ranks,
        ),
        packet_identity=packet_id,
    )


def build_packet_for_query(
    *,
    corpus: Corpus,
    retriever: BM25Retriever,
    query: str,
    config: RetrievalConfig,
    max_items: int | None = None,
    max_tokens: int = 2000,
    expand_section: bool = False,
    aperture_id: str | None = None,
) -> EvidencePacket:
    """Run the configured maintained retriever and assemble its evidence packet."""
    hits = query_retriever(retriever, query, config)
    return build_evidence_packet(
        corpus=corpus,
        query=query,
        hits=hits,
        config=config,
        max_items=max_items,
        max_tokens=max_tokens,
        expand_section=expand_section,
        aperture_id=aperture_id,
    )
