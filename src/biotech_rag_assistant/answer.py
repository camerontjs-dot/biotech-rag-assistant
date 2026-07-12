"""Deterministic extractive answer assembly for retrieved chunks."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from biotech_rag_assistant.citations import (
    AnswerCitation,
    AnswerFixture,
    CitationOutcome,
    CitationValidationResult,
    RetrievedChunkRecord,
    RetrievedResultsPayload,
    validate_answer_citations,
)
from biotech_rag_assistant.models import RetrievalHit

REFUSAL_TEXT = "The retrieved documents do not contain enough information to answer this question."


class AnswerAssemblyError(Exception):
    """Raised when generated answer citations fail the structural contract."""


class ExtractiveAnswer(BaseModel):
    """Source-bound answer assembled from retrieved chunks."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    outcome: CitationOutcome
    answer_text: str = Field(min_length=1)
    citations: list[AnswerCitation] = Field(default_factory=list)
    retrieved_chunks: list[dict[str, object]] = Field(default_factory=list)
    citation_validation: CitationValidationResult

    def to_cli_record(self) -> dict[str, object]:
        return {
            "query": self.query,
            "outcome": self.outcome,
            "answer_text": self.answer_text,
            "citations": [citation.model_dump() for citation in self.citations],
            "retrieved_chunks": self.retrieved_chunks,
            "citation_validation": self.citation_validation.to_cli_record(),
        }


def build_extractive_answer(query: str, hits: list[RetrievalHit]) -> ExtractiveAnswer:
    """Build a deterministic answer by copying retrieved chunk text."""
    records = [hit.to_cli_record() for hit in hits]
    if not hits:
        answer_text = REFUSAL_TEXT
        citations: list[AnswerCitation] = []
        outcome: CitationOutcome = "refusal"
    else:
        blocks = []
        citations = []
        for index, hit in enumerate(hits, start=1):
            label = str(index)
            chunk = hit.chunk
            blocks.append(
                f"[source: {label}] {chunk.doc_id} v{chunk.version}, "
                f"{chunk.section_heading}, {chunk.line_or_page_span}\n{chunk.text}"
            )
            citations.append(AnswerCitation(chunk_id=chunk.chunk_id, label=label))
        answer_text = "\n\n".join(blocks)
        outcome = "answer"

    retrieved_payload = RetrievedResultsPayload(
        query=query,
        hits=[RetrievedChunkRecord.model_validate(record) for record in records],
    )
    answer_fixture = AnswerFixture(
        answer_text=answer_text,
        citations=citations,
        expected_outcome=outcome,
    )
    citation_validation = validate_answer_citations(retrieved_payload, answer_fixture)
    if not citation_validation.valid:
        raise AnswerAssemblyError("generated answer citations failed validation")

    return ExtractiveAnswer(
        query=query,
        outcome=outcome,
        answer_text=answer_text,
        citations=citations,
        retrieved_chunks=records,
        citation_validation=citation_validation,
    )
