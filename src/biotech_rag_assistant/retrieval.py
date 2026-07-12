"""BM25 retrieval over approved/effective controlled-document chunks."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from rank_bm25 import BM25Okapi

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.models import DocumentChunk, RetrievalHit, SourceDocument

TOKEN_RE = re.compile(r"\w+")


class RetrievalConfig(BaseModel):
    """Shared retrieval settings for CLI, evaluation, and answer assembly."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["bm25"] = "bm25"
    top_k: int = Field(default=5, ge=1)
    score_floor: float = Field(default=0.0, ge=0.0)
    min_top_coverage: float = Field(default=0.6, ge=0.0, le=1.0)

    def to_cli_record(self) -> dict[str, object]:
        return self.model_dump()


def tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer used by the deterministic BM25 baseline."""
    return TOKEN_RE.findall(text.lower())


# Generic, domain-safe stopwords removed before measuring query-term coverage.
# Deliberately excludes controlled-document vocabulary (status, version, approved,
# document, procedure, record, quality, ...), which must count toward relevance.
STOPWORDS = frozenset(
    """
    a an the of for to and or in on is are was were be been being this that these those
    what which who whom how when where why do does did we you they it its our your their
    with without within into onto from by as at if then than so such not no can could should
    would will may might must have has had i me my them he she his her him us about over under
    """.split()
)


def content_terms(text: str) -> set[str]:
    """Distinct non-stopword query tokens used to measure relevance coverage."""
    return {token for token in tokenize(text) if token not in STOPWORDS and len(token) > 1}


def coverage(query_text: str, chunk_text: str) -> float:
    """Fraction of the query's distinctive terms that appear in a chunk (0.0-1.0)."""
    query_terms = content_terms(query_text)
    if not query_terms:
        return 0.0
    chunk_tokens = set(tokenize(chunk_text))
    return len(query_terms & chunk_tokens) / len(query_terms)


def index_text(chunk: DocumentChunk) -> str:
    r"""The string indexed and relevance-gated for a chunk: section heading + verbatim span.

    ``chunk.text`` is the exact cited source span (``raw[char_start:char_end]``, ADR-016). The
    section heading is folded in only here, at index/scoring time, so heading terms stay
    matchable for BM25 and the coverage gate without the cited quote disagreeing with its own
    offsets. The result is byte-identical to the pre-ADR-016 ``heading + "\n" + body`` text, so
    BM25 ranking and the 0.6 coverage calibration are unchanged.
    """
    return f"{chunk.section_heading}\n{chunk.text}"


class BM25Retriever:
    """Thin wrapper around rank-bm25 with deterministic tie-breaking."""

    def __init__(self, chunks: list[DocumentChunk]) -> None:
        self.chunks = list(chunks)
        self._corpus_tokens = [tokenize(index_text(chunk)) for chunk in self.chunks]
        self._bm25 = BM25Okapi(self._corpus_tokens) if self.chunks else None

    def query(
        self,
        query_text: str,
        *,
        top_k: int = 5,
        score_floor: float = 0.0,
        min_top_coverage: float = 0.0,
    ) -> list[RetrievalHit]:
        query_tokens = tokenize(query_text)
        if not query_tokens or self._bm25 is None:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(self.chunks)),
            key=lambda index: (
                -float(scores[index]),
                self.chunks[index].doc_id,
                self.chunks[index].chunk_index,
                self.chunks[index].chunk_id,
            ),
        )

        hits: list[RetrievalHit] = []
        for index in ranked_indices:
            score = float(scores[index])
            if score <= score_floor:
                continue
            hits.append(
                RetrievalHit(
                    rank=len(hits) + 1,
                    score=score,
                    chunk=self.chunks[index],
                )
            )
            if len(hits) >= top_k:
                break

        # Lexical relevance gate (ADR-012). BM25 returns positive scores for incidental
        # token overlap, so an off-topic question can otherwise surface a loosely related
        # approved passage that the extractive answer copies verbatim with valid citations.
        # Require the top-ranked passage to actually contain enough of the question's
        # distinctive terms; otherwise refuse (return no hits). Gating on rank 1 keeps the
        # decision independent of top_k and fails toward refusal.
        if hits and min_top_coverage > 0.0:
            if coverage(query_text, index_text(hits[0].chunk)) < min_top_coverage:
                return []
        return hits


def build_retriever(documents: list[SourceDocument], *, method: str = "bm25") -> BM25Retriever:
    """Chunk and index a corpus once into a reusable retriever.

    Building the BM25 index is the expensive step, and it depends only on the corpus, not on the
    query. Build it once per corpus (at API startup, or once before an evaluation loop) and reuse
    it via ``query_retriever``; only genuinely one-shot callers should use ``run_retrieval``.
    """
    if method != "bm25":
        raise ValueError(f"unsupported retrieval method: {method}")
    return BM25Retriever(chunk_documents(documents))


def query_retriever(
    retriever: BM25Retriever,
    query_text: str,
    config: RetrievalConfig,
) -> list[RetrievalHit]:
    """Query a prebuilt retriever with a config's query-time parameters."""
    return retriever.query(
        query_text,
        top_k=config.top_k,
        score_floor=config.score_floor,
        min_top_coverage=config.min_top_coverage,
    )


def run_retrieval(
    documents: list[SourceDocument],
    query_text: str,
    config: RetrievalConfig,
) -> list[RetrievalHit]:
    """One-shot convenience: build a retriever for ``documents`` and run a single query.

    For repeated queries over the same corpus, build once with ``build_retriever`` and reuse it
    with ``query_retriever`` rather than paying the chunk + index cost on every call.
    """
    return query_retriever(build_retriever(documents, method=config.method), query_text, config)
