"""Typed retrieval nominations and deterministic EvidencePacket v1 assembly."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.models import (
    RETRIEVABLE_STATUSES,
    Corpus,
    DocumentChunk,
    DocumentType,
    RetrievalHit,
)
from biotech_rag_assistant.retrieval import RetrievalConfig

NominationKind = Literal[
    "chunk",
    "section_expansion",
    "cross_reference_admission",
]
RepresentationLevel = Literal["chunk", "section", "document"]
RetrievalSignal = Literal["bm25", "semantic", "hybrid", "rerank"]
AuthorityClass = Literal[
    "policy",
    "specification",
    "procedure",
    "technical_note",
    "calibration_note",
    "training_note",
    "example",
]
SectionRole = Literal[
    "normative",
    "definitions",
    "responsibilities",
    "references",
    "revision_history",
]

AUTHORITY_CLASS: dict[DocumentType, AuthorityClass] = {
    "Policy": "policy",
    "Specification": "specification",
    "SOP": "procedure",
    "TechnicalNote": "technical_note",
    "CalibrationNote": "calibration_note",
    "TrainingNote": "training_note",
    "DeviationExample": "example",
}
WHITESPACE_RE = re.compile(r"\s+")


class RetrievalReason(BaseModel):
    """One method-specific reason a source span was nominated."""

    model_config = ConfigDict(extra="forbid")

    signal: RetrievalSignal
    rank: int = Field(ge=1)
    raw_score: float


class RetrievalNomination(BaseModel):
    """Typed pre-admission nomination over an exact source span."""

    model_config = ConfigDict(extra="forbid")

    nomination_id: str
    query_id: str
    chunk_id: str
    doc_id: str
    version: str
    status: str
    source_hash: str
    char_start: int = Field(ge=0)
    char_end: int = Field(gt=0)
    section_heading: str
    retrieval_signal: RetrievalSignal
    raw_score: float
    rank: int = Field(ge=1)
    retrieval_config_id: str
    corpus_identity: str
    nomination_kind: NominationKind = "chunk"
    retrieval_reasons: list[RetrievalReason]
    representation_level: RepresentationLevel = "chunk"
    section_role: SectionRole | None = None
    authority_class: AuthorityClass
    token_estimate: int = Field(ge=0)
    expansion_handle: str
    parent_context_id: str | None = None
    authorization_scope: str | None = None
    text: str

    def identity_tuple(self) -> tuple[object, ...]:
        """Fields admitted into the ep1 identity payload."""
        return (
            self.chunk_id,
            self.doc_id,
            self.version,
            self.status,
            self.source_hash,
            self.char_start,
            self.char_end,
            self.nomination_kind,
        )


class EvidenceBudget(BaseModel):
    """Deterministic packet admission limits."""

    model_config = ConfigDict(extra="forbid")

    max_items: int = Field(default=3, ge=1)
    max_context_chars: int = Field(default=12_000, ge=1)
    expand_sections: bool = False


class EvidencePacket(BaseModel):
    """Immutable source-only packet assembled after mechanical admission."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["ep1"] = "ep1"
    packet_id: str
    query: str
    query_id: str
    corpus_identity: str
    retrieval_config_id: str
    aperture_id: str | None = None
    admitted_nominations: list[RetrievalNomination]
    exclusion_summary: dict[str, int]
    evidence_budget: EvidenceBudget
    diagnostics: dict[str, object]

    def to_record(self) -> dict[str, object]:
        return self.model_dump()


def canonical_json(value: object) -> bytes:
    """Canonical UTF-8 JSON used for all stable identities."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def stable_hash(prefix: str, value: object) -> str:
    return f"{prefix}:{hashlib.sha256(canonical_json(value)).hexdigest()}"


def normalize_query(query: str) -> str:
    """Trim and collapse whitespace without changing case or punctuation."""
    return WHITESPACE_RE.sub(" ", query.strip())


def make_query_id(query: str) -> str:
    return stable_hash("q1", normalize_query(query))


def retrieval_config_id(config: RetrievalConfig) -> str:
    return stable_hash("rc1", config.model_dump(mode="json"))


def corpus_identity(corpus: Corpus) -> str:
    """Hash an explicit corpus manifest or a derived legacy manifest."""
    manifest_candidates = (
        corpus.corpus_dir / "corpus_manifest.json",
        corpus.corpus_dir.parent / "corpus_manifest.json",
    )
    for manifest_path in manifest_candidates:
        if manifest_path.exists():
            digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
            return f"cm1:file:{digest}"

    records = [
        {
            "doc_id": document.metadata.doc_id,
            "version": document.metadata.version,
            "status": document.metadata.status,
            "source_hash": document.metadata.source_hash,
            "source_file_path": str(document.metadata.source_file_path),
        }
        for document in sorted(
            corpus.documents,
            key=lambda item: (
                item.metadata.doc_id,
                item.metadata.version,
                item.metadata.status,
                str(item.metadata.source_file_path),
            ),
        )
    ]
    digest = hashlib.sha256(canonical_json({"documents": records})).hexdigest()
    return f"cm1:derived:{digest}"


def token_estimate(text: str) -> int:
    """Model-agnostic deterministic approximation, excluded from ep1 identity."""
    return math.ceil(len(text.encode("utf-8")) / 4)


def infer_section_role(heading: str) -> SectionRole | None:
    lowered = heading.strip().lower()
    if "definition" in lowered:
        return "definitions"
    if "responsibilit" in lowered:
        return "responsibilities"
    if "reference" in lowered:
        return "references"
    if "revision" in lowered or "change history" in lowered:
        return "revision_history"
    if any(
        marker in lowered
        for marker in (
            "procedure",
            "requirement",
            "acceptance",
            "limit",
            "specification",
            "process",
            "control",
        )
    ):
        return "normative"
    return None


def _nomination_id(
    *,
    query_id: str,
    chunk: DocumentChunk,
    signal: RetrievalSignal,
    retrieval_config: str,
    corpus: str,
    nomination_kind: NominationKind,
) -> str:
    return stable_hash(
        "nom1",
        {
            "query_id": query_id,
            "chunk_id": chunk.chunk_id,
            "doc_id": chunk.doc_id,
            "version": chunk.version,
            "source_hash": chunk.source_hash,
            "char_start": chunk.char_start,
            "char_end": chunk.char_end,
            "retrieval_signal": signal,
            "retrieval_config_id": retrieval_config,
            "corpus_identity": corpus,
            "nomination_kind": nomination_kind,
        },
    )


def nomination_from_hit(
    hit: RetrievalHit,
    *,
    query_id: str,
    retrieval_config: str,
    corpus: str,
    signal: RetrievalSignal = "bm25",
) -> RetrievalNomination:
    chunk = hit.chunk
    nomination_id = _nomination_id(
        query_id=query_id,
        chunk=chunk,
        signal=signal,
        retrieval_config=retrieval_config,
        corpus=corpus,
        nomination_kind="chunk",
    )
    return RetrievalNomination(
        nomination_id=nomination_id,
        query_id=query_id,
        chunk_id=chunk.chunk_id,
        doc_id=chunk.doc_id,
        version=chunk.version,
        status=chunk.status,
        source_hash=chunk.source_hash,
        char_start=chunk.char_start,
        char_end=chunk.char_end,
        section_heading=chunk.section_heading,
        retrieval_signal=signal,
        raw_score=hit.score,
        rank=hit.rank,
        retrieval_config_id=retrieval_config,
        corpus_identity=corpus,
        retrieval_reasons=[
            RetrievalReason(signal=signal, rank=hit.rank, raw_score=hit.score)
        ],
        section_role=infer_section_role(chunk.section_heading),
        authority_class=AUTHORITY_CLASS[chunk.doc_type],
        token_estimate=token_estimate(chunk.text),
        expansion_handle=(
            f"section:{chunk.doc_id}:{chunk.version}:{chunk.section_heading}"
        ),
        text=chunk.text,
    )


def _section_expansions(
    parent: RetrievalNomination,
    chunks: list[DocumentChunk],
) -> list[RetrievalNomination]:
    matches = [
        chunk
        for chunk in chunks
        if chunk.doc_id == parent.doc_id
        and chunk.version == parent.version
        and chunk.section_heading == parent.section_heading
        and chunk.chunk_id != parent.chunk_id
    ]
    result = []
    for index, chunk in enumerate(matches, start=1):
        nomination_id = _nomination_id(
            query_id=parent.query_id,
            chunk=chunk,
            signal=parent.retrieval_signal,
            retrieval_config=parent.retrieval_config_id,
            corpus=parent.corpus_identity,
            nomination_kind="section_expansion",
        )
        result.append(
            RetrievalNomination(
                nomination_id=nomination_id,
                query_id=parent.query_id,
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                version=chunk.version,
                status=chunk.status,
                source_hash=chunk.source_hash,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                section_heading=chunk.section_heading,
                retrieval_signal=parent.retrieval_signal,
                raw_score=parent.raw_score,
                rank=parent.rank + index,
                retrieval_config_id=parent.retrieval_config_id,
                corpus_identity=parent.corpus_identity,
                nomination_kind="section_expansion",
                retrieval_reasons=parent.retrieval_reasons,
                representation_level="section",
                section_role=infer_section_role(chunk.section_heading),
                authority_class=AUTHORITY_CLASS[chunk.doc_type],
                token_estimate=token_estimate(chunk.text),
                expansion_handle=parent.expansion_handle,
                parent_context_id=parent.nomination_id,
                text=chunk.text,
            )
        )
    return result


def _packet_identity_payload(
    *,
    query: str,
    corpus: str,
    retrieval_config: str,
    aperture_id: str | None,
    admitted: list[RetrievalNomination],
    exclusion_summary: dict[str, int],
) -> dict[str, object]:
    return {
        "schema_version": "ep1",
        "query": query,
        "corpus_identity": corpus,
        "retrieval_config_id": retrieval_config,
        "aperture_id": aperture_id,
        "admitted_items": [list(item.identity_tuple()) for item in admitted],
        "exclusion_summary": dict(sorted(exclusion_summary.items())),
    }


def build_evidence_packet(
    corpus: Corpus,
    query: str,
    hits: list[RetrievalHit],
    retrieval_config: RetrievalConfig,
    *,
    aperture_id: str | None = None,
    budget: EvidenceBudget | None = None,
) -> EvidencePacket:
    """Convert retrieval output into a deterministic admitted source packet."""
    budget = budget or EvidenceBudget()
    normalized_query = normalize_query(query)
    query_id = make_query_id(normalized_query)
    config_id = retrieval_config_id(retrieval_config)
    corpus_id = corpus_identity(corpus)

    nominations = [
        nomination_from_hit(
            hit,
            query_id=query_id,
            retrieval_config=config_id,
            corpus=corpus_id,
        )
        for hit in hits
    ]
    if budget.expand_sections:
        all_chunks = chunk_documents(corpus.documents)
        expanded: list[RetrievalNomination] = []
        for nomination in nominations:
            expanded.append(nomination)
            expanded.extend(_section_expansions(nomination, all_chunks))
        nominations = expanded

    exclusions: Counter[str] = Counter()
    admitted: list[RetrievalNomination] = []
    seen_spans: set[tuple[str, int, int]] = set()
    context_chars = 0

    for nomination in nominations:
        if nomination.status not in RETRIEVABLE_STATUSES:
            exclusions["status_not_retrievable"] += 1
            continue

        span_key = (
            nomination.source_hash,
            nomination.char_start,
            nomination.char_end,
        )
        if span_key in seen_spans:
            exclusions["duplicate_source_span"] += 1
            continue

        if len(admitted) >= budget.max_items:
            exclusions["item_budget_exhausted"] += 1
            continue

        next_chars = context_chars + len(nomination.text)
        if next_chars > budget.max_context_chars:
            exclusions["context_budget_exhausted"] += 1
            continue

        admitted.append(nomination)
        seen_spans.add(span_key)
        context_chars = next_chars

    exclusion_summary = dict(sorted(exclusions.items()))
    identity_payload = _packet_identity_payload(
        query=normalized_query,
        corpus=corpus_id,
        retrieval_config=config_id,
        aperture_id=aperture_id,
        admitted=admitted,
        exclusion_summary=exclusion_summary,
    )
    packet_id = stable_hash("ep1", identity_payload)

    diagnostics: dict[str, object] = {
        "scores_excluded_from_identity": True,
        "context_chars": context_chars,
        "nomination_count_before_admission": len(nominations),
        "admitted_count": len(admitted),
        "raw_scores": {
            item.nomination_id: {
                "rank": item.rank,
                "raw_score": item.raw_score,
                "retrieval_signal": item.retrieval_signal,
            }
            for item in admitted
        },
    }
    return EvidencePacket(
        packet_id=packet_id,
        query=normalized_query,
        query_id=query_id,
        corpus_identity=corpus_id,
        retrieval_config_id=config_id,
        aperture_id=aperture_id,
        admitted_nominations=admitted,
        exclusion_summary=exclusion_summary,
        evidence_budget=budget,
        diagnostics=diagnostics,
    )


def replace_scores_for_test(
    packet: EvidencePacket,
    scores: list[float],
) -> EvidencePacket:
    """Test helper: change diagnostics while preserving admitted source identities."""
    if len(scores) != len(packet.admitted_nominations):
        raise ValueError("score count must equal admitted nomination count")
    data = packet.model_dump()
    for nomination, score in zip(
        data["admitted_nominations"],
        scores,
        strict=True,
    ):
        nomination["raw_score"] = score
        nomination["retrieval_reasons"][0]["raw_score"] = score
    data["diagnostics"]["raw_scores"] = {
        nomination["nomination_id"]: {
            "rank": nomination["rank"],
            "raw_score": nomination["raw_score"],
            "retrieval_signal": nomination["retrieval_signal"],
        }
        for nomination in data["admitted_nominations"]
    }
    return EvidencePacket.model_validate(data)


def manifest_hash_for_path(corpus_dir: Path) -> str:
    """Small inspection helper for tests and operator receipts."""
    manifest = corpus_dir / "corpus_manifest.json"
    if not manifest.exists():
        raise FileNotFoundError(manifest)
    return hashlib.sha256(manifest.read_bytes()).hexdigest()
