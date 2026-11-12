"""Evidence for one chat turn: admitted passages only, with provenance re-checked per turn.

Evidence comes exclusively from the maintained retrieval path (status gate ADR-005, coverage gate
ADR-012, maintained ``RetrievalConfig`` defaults). Before a passage is supplied to a model, its
status, source hash, and exact-span invariant (ADR-016: ``text == raw_text[char_start:char_end]``)
are re-verified against the loaded corpus; any mismatch fails the turn closed.

Section headings are kept for display but are never sent to a model as evidence (heading
semantic-authority exclusion): a heading must not supply a proposition the body text lacks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from biotech_rag_assistant.models import (
    RETRIEVABLE_STATUSES,
    Corpus,
    DocumentChunk,
    RetrievalHit,
    SourceDocument,
)
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    build_status_blind_retriever,
    held_out_hits,
    index_text,
    tokenize,
)

SNAPSHOT_NOTE = (
    "Documents were loaded and validated once, at server start. Status or content changes on "
    "disk take effect only after a restart; a conversation does not track revocations."
)


class EvidenceBoundaryError(Exception):
    """A retrieved passage failed a provenance or admissibility re-check."""


class CorpusSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    corpus: str
    snapshot_id: str
    loaded_at: str
    documents_valid: int
    documents_retrievable: int
    documents_excluded: int
    note: str = SNAPSHOT_NOTE


class EvidencePassage(BaseModel):
    """One admitted passage supplied for a turn. Every field comes from trusted corpus data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    ref: str
    chunk_id: str
    doc_id: str
    doc_title: str
    doc_type: str
    version: str
    status: str
    effective_date: str
    department: str
    section_heading: str
    source_file_path: str
    source_hash: str
    line_or_page_span: str
    char_start: int
    char_end: int
    text: str
    best_rank: int
    best_score: float
    retrieved_by: list[str]

    def model_payload(self) -> dict[str, object]:
        """What a model sees: identity metadata and the exact body span. No section heading."""
        return {
            "ref": self.ref,
            "document": {
                "doc_id": self.doc_id,
                "title": self.doc_title,
                "version": self.version,
                "status": self.status,
                "effective_date": self.effective_date,
            },
            "text": self.text,
        }

    @property
    def label(self) -> str:
        return f"{self.doc_id} v{self.version}"


HeldOutReason = Literal["status_blind_match", "named_in_message"]


class HeldOutPointer(BaseModel):
    """Identity of a held-out (Draft/Obsolete/Superseded) document relevant to a turn.

    Reasons: a status-blind run of the same query would have answered from it (ADR-018), and/or
    the user named it. The pointer carries identity and status only: no passage text. It is
    never supplied to a model as evidence and is never cited.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    doc_id: str
    doc_title: str
    version: str
    status: str
    reasons: list[HeldOutReason]
    status_blind_rank: int | None = None

    def identity_payload(self) -> dict[str, object]:
        return {
            "doc_id": self.doc_id,
            "title": self.doc_title,
            "version": self.version,
            "status": self.status,
            "admitted": False,
        }


@dataclass(frozen=True)
class CorpusBinding:
    """A loaded corpus plus the indexes the chat engine needs, built once at startup."""

    name: str
    corpus: Corpus
    retriever: BM25Retriever
    status_blind: BM25Retriever
    snapshot: CorpusSnapshot
    documents_by_key: dict[tuple[str, str], SourceDocument]
    vocabulary: frozenset[str]

    @classmethod
    def build(
        cls, name: str, corpus: Corpus, retriever: BM25Retriever, loaded_at: datetime
    ) -> CorpusBinding:
        return cls(
            name=name,
            corpus=corpus,
            retriever=retriever,
            status_blind=build_status_blind_retriever(corpus.documents),
            snapshot=corpus_snapshot(name, corpus, loaded_at),
            documents_by_key={
                (document.metadata.doc_id, document.metadata.version): document
                for document in corpus.documents
            },
            vocabulary=frozenset(
                token for chunk in retriever.chunks for token in tokenize(index_text(chunk))
            ),
        )


def corpus_snapshot(name: str, corpus: Corpus, loaded_at: datetime) -> CorpusSnapshot:
    """Fingerprint every valid document's identity, status, and hash as loaded."""
    entries = sorted(
        (
            document.metadata.doc_id,
            document.metadata.version,
            document.metadata.status,
            document.metadata.source_hash,
        )
        for document in corpus.documents
    )
    digest = hashlib.sha256(json.dumps(entries).encode("utf-8")).hexdigest()
    return CorpusSnapshot(
        corpus=name,
        snapshot_id=f"sha256:{digest[:16]}",
        loaded_at=loaded_at.isoformat(timespec="seconds"),
        documents_valid=corpus.report.documents_valid,
        documents_retrievable=corpus.report.documents_retrievable,
        documents_excluded=corpus.report.documents_excluded,
    )


@dataclass
class _Candidate:
    chunk: DocumentChunk
    rank: int
    score: float
    first_seen: int
    origins: list[str]


def assemble_evidence(
    attempts: list[tuple[str, list[RetrievalHit]]],
    binding: CorpusBinding,
    max_passages: int,
) -> list[EvidencePassage]:
    """Merge retrieval attempts into ref-labelled passages, re-verifying provenance.

    Passages are de-duplicated by ``chunk_id`` and capped at ``max_passages`` by best rank.
    Documents are ordered by their best rank; passages within a document keep source order, so a
    procedure's steps reach the model in the order the document states them.
    """
    candidates: dict[str, _Candidate] = {}
    for origin, hits in attempts:
        for hit in hits:
            chunk = hit.chunk
            if chunk.status not in RETRIEVABLE_STATUSES:
                raise EvidenceBoundaryError(
                    f"retrieval returned non-retrievable chunk {chunk.chunk_id} ({chunk.status})"
                )
            existing = candidates.get(chunk.chunk_id)
            if existing is None:
                candidates[chunk.chunk_id] = _Candidate(
                    chunk=chunk,
                    rank=hit.rank,
                    score=hit.score,
                    first_seen=len(candidates),
                    origins=[origin],
                )
                continue
            if origin not in existing.origins:
                existing.origins.append(origin)
            if hit.rank < existing.rank:
                existing.rank, existing.score = hit.rank, hit.score

    by_rank = sorted(candidates.values(), key=lambda c: (c.rank, c.first_seen))
    selected = by_rank[:max_passages]
    doc_order: dict[str, int] = {}
    for candidate in selected:
        doc_order.setdefault(candidate.chunk.doc_id, len(doc_order))
    ordered = sorted(
        selected, key=lambda c: (doc_order[c.chunk.doc_id], c.chunk.chunk_index)
    )

    passages: list[EvidencePassage] = []
    for index, candidate in enumerate(ordered, start=1):
        chunk = candidate.chunk
        document = binding.documents_by_key.get((chunk.doc_id, chunk.version))
        if document is None:
            raise EvidenceBoundaryError(f"chunk {chunk.chunk_id} has no loaded source document")
        _verify_provenance(chunk, document)
        passages.append(
            EvidencePassage(
                ref=f"S{index}",
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                doc_title=chunk.doc_title,
                doc_type=chunk.doc_type,
                version=chunk.version,
                status=chunk.status,
                effective_date=document.metadata.effective_date.isoformat(),
                department=chunk.department,
                section_heading=chunk.section_heading,
                source_file_path=str(chunk.source_file_path),
                source_hash=chunk.source_hash,
                line_or_page_span=chunk.line_or_page_span,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                text=chunk.text,
                best_rank=candidate.rank,
                best_score=candidate.score,
                retrieved_by=list(candidate.origins),
            )
        )
    return passages


def _verify_provenance(chunk: DocumentChunk, document: SourceDocument) -> None:
    if not document.is_retrievable:
        raise EvidenceBoundaryError(f"{chunk.doc_id} v{chunk.version} is not retrievable")
    if (
        document.metadata.source_hash != chunk.source_hash
        or document.computed_source_hash != chunk.source_hash
    ):
        raise EvidenceBoundaryError(f"source hash mismatch for {chunk.chunk_id}")
    if document.raw_text[chunk.char_start : chunk.char_end] != chunk.text:
        raise EvidenceBoundaryError(f"cited span does not match source text for {chunk.chunk_id}")


def held_out_pointers(
    binding: CorpusBinding,
    *,
    message: str,
    query: str | None,
    config: RetrievalConfig,
) -> list[HeldOutPointer]:
    """Held-out documents for a turn: status-blind matches of ``query`` and ids the user named.

    ``query`` is ``None`` when the turn had admitted evidence: the status-blind explanation is
    only for refusals (ADR-018). Named held-out documents are reported either way, so a request
    about a retired SOP is answered with its status rather than with silence.
    """
    pointers: dict[str, HeldOutPointer] = {}
    if query:
        for hit in held_out_hits(binding.status_blind, query, config):
            chunk = hit.chunk
            if chunk.doc_id not in pointers:
                pointers[chunk.doc_id] = HeldOutPointer(
                    doc_id=chunk.doc_id,
                    doc_title=chunk.doc_title,
                    version=chunk.version,
                    status=chunk.status,
                    reasons=["status_blind_match"],
                    status_blind_rank=hit.rank,
                )
    message_tokens = tokenize(message)
    for document in binding.corpus.documents:
        metadata = document.metadata
        if document.is_retrievable or not _mentions(message_tokens, tokenize(metadata.doc_id)):
            continue
        existing = pointers.get(metadata.doc_id)
        if existing is not None:
            pointers[metadata.doc_id] = existing.model_copy(
                update={"reasons": [*existing.reasons, "named_in_message"]}
            )
            continue
        pointers[metadata.doc_id] = HeldOutPointer(
            doc_id=metadata.doc_id,
            doc_title=metadata.doc_title,
            version=metadata.version,
            status=metadata.status,
            reasons=["named_in_message"],
        )
    return list(pointers.values())


def _mentions(tokens: list[str], needle: list[str]) -> bool:
    """True when ``needle`` occurs as a contiguous token run ("SOP-QA-009" or "sop qa 009")."""
    if not needle:
        return False
    width = len(needle)
    return any(tokens[i : i + width] == needle for i in range(len(tokens) - width + 1))
