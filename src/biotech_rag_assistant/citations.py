"""Citation-resolution checks for retrieved controlled-document chunks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from biotech_rag_assistant.models import RETRIEVABLE_STATUSES, DocumentStatus

CitationOutcome = Literal["answer", "refusal"]
ModelT = TypeVar("ModelT", bound=BaseModel)


class CitationFixtureError(Exception):
    """Raised when a retrieved-result or answer fixture cannot be loaded."""


class AnswerCitation(BaseModel):
    """One structured answer citation."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: str = Field(min_length=1)
    label: str | None = Field(default=None, min_length=1)


class AnswerFixture(BaseModel):
    """Hand-written answer fixture used before answer generation exists."""

    model_config = ConfigDict(extra="forbid")

    answer_text: str = Field(min_length=1)
    citations: list[AnswerCitation] = Field(default_factory=list)
    expected_outcome: CitationOutcome


class RetrievedChunkRecord(BaseModel):
    """Minimum retrieved-result fields needed for citation validation."""

    model_config = ConfigDict(extra="allow")

    chunk_id: str = Field(min_length=1)
    status: DocumentStatus


class RetrievedResultsPayload(BaseModel):
    """Machine-readable retrieval payload emitted by the retrieval CLI."""

    model_config = ConfigDict(extra="allow")

    query: str | None = None
    hits: list[RetrievedChunkRecord] = Field(default_factory=list)


class CitationIssue(BaseModel):
    """One citation-resolution issue."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    chunk_id: str | None = None


class CitationValidationResult(BaseModel):
    """Result of checking answer citations against retrieved chunks."""

    model_config = ConfigDict(extra="forbid")

    metric_name: Literal["citation_resolves_to_retrieved_chunk"] = (
        "citation_resolves_to_retrieved_chunk"
    )
    citation_resolves_to_retrieved_chunk: bool
    expected_outcome: CitationOutcome
    answer_citation_count: int = Field(ge=0)
    retrieved_chunk_count: int = Field(ge=0)
    resolved_citation_count: int = Field(ge=0)
    issues: list[CitationIssue] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return self.citation_resolves_to_retrieved_chunk and not self.issues

    def to_cli_record(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "metric_name": self.metric_name,
            "citation_resolves_to_retrieved_chunk": self.citation_resolves_to_retrieved_chunk,
            "expected_outcome": self.expected_outcome,
            "answer_citation_count": self.answer_citation_count,
            "retrieved_chunk_count": self.retrieved_chunk_count,
            "resolved_citation_count": self.resolved_citation_count,
            "issues": [issue.model_dump() for issue in self.issues],
        }


def load_answer_fixture(path: Path) -> AnswerFixture:
    """Load a hand-written answer fixture from JSON."""
    return _load_json_model(path, AnswerFixture)


def load_retrieved_results(path: Path) -> RetrievedResultsPayload:
    """Load a retrieved-result payload from JSON."""
    return _load_json_model(path, RetrievedResultsPayload)


def validate_answer_citations(
    retrieved_results: RetrievedResultsPayload,
    answer_fixture: AnswerFixture,
) -> CitationValidationResult:
    """Check citation IDs against retrieved chunks without assessing semantic support."""
    retrieved_by_chunk_id = {hit.chunk_id: hit for hit in retrieved_results.hits}
    issues: list[CitationIssue] = []

    stale_hits = [
        hit for hit in retrieved_results.hits if hit.status not in RETRIEVABLE_STATUSES
    ]
    for hit in stale_hits:
        issues.append(
            CitationIssue(
                code="stale_retrieved_chunk",
                chunk_id=hit.chunk_id,
                message=f"retrieved chunk status is not retrievable: {hit.status}",
            )
        )

    if answer_fixture.expected_outcome == "answer" and not answer_fixture.citations:
        issues.append(
            CitationIssue(
                code="missing_answer_citation",
                message="answer fixtures must cite at least one retrieved chunk",
            )
        )

    if answer_fixture.expected_outcome == "refusal" and answer_fixture.citations:
        issues.append(
            CitationIssue(
                code="refusal_has_citation",
                message="refusal fixtures must not cite retrieved chunks",
            )
        )

    resolved_count = 0
    unresolved_count = 0
    for citation in answer_fixture.citations:
        retrieved = retrieved_by_chunk_id.get(citation.chunk_id)
        if retrieved is None:
            unresolved_count += 1
            issues.append(
                CitationIssue(
                    code="unresolved_citation",
                    chunk_id=citation.chunk_id,
                    message="citation chunk_id was not present in retrieved results",
                )
            )
            continue

        resolved_count += 1
        if retrieved.status not in RETRIEVABLE_STATUSES:
            issues.append(
                CitationIssue(
                    code="stale_citation",
                    chunk_id=citation.chunk_id,
                    message=f"citation resolved to non-retrievable status: {retrieved.status}",
                )
            )

    citation_resolves = unresolved_count == 0
    if answer_fixture.expected_outcome == "answer" and not answer_fixture.citations:
        citation_resolves = False

    return CitationValidationResult(
        citation_resolves_to_retrieved_chunk=citation_resolves,
        expected_outcome=answer_fixture.expected_outcome,
        answer_citation_count=len(answer_fixture.citations),
        retrieved_chunk_count=len(retrieved_results.hits),
        resolved_citation_count=resolved_count,
        issues=issues,
    )


def _load_json_model(path: Path, model_type: type[ModelT]) -> ModelT:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CitationFixtureError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise CitationFixtureError(f"invalid JSON in {path}: {exc}") from exc

    try:
        return model_type.model_validate(raw)
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            messages.append(f"{field}: {error['msg']}")
        raise CitationFixtureError(f"invalid fixture {path}: {'; '.join(messages)}") from exc
