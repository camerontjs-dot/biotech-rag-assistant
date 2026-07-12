"""Typed records for controlled-document ingest and retrieval."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

NonBlankStr = Annotated[str, Field(min_length=1)]
HashValue = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]

DocumentStatus = Literal["Approved", "Effective", "Draft", "Obsolete", "Superseded"]
DocumentType = Literal[
    "SOP",
    "Policy",
    "TrainingNote",
    "DeviationExample",
    "CalibrationNote",
    "Specification",
    "TechnicalNote",
]

RETRIEVABLE_STATUSES = {"Approved", "Effective"}


class DocumentMetadata(BaseModel):
    """Sidecar metadata required before a source can be indexed."""

    model_config = ConfigDict(extra="forbid")

    doc_id: NonBlankStr
    doc_title: NonBlankStr
    doc_type: DocumentType
    version: NonBlankStr
    status: DocumentStatus
    effective_date: date
    review_due_date: date | None = None
    department: NonBlankStr
    source_file_path: Path
    source_hash: HashValue

    @field_validator("doc_id", "doc_title", "version", "department")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("field must not be blank")
        return stripped

    @model_validator(mode="after")
    def validate_review_due_date(self) -> DocumentMetadata:
        if self.review_due_date is not None and self.review_due_date < self.effective_date:
            raise ValueError("review_due_date must not be earlier than effective_date")
        return self

    @property
    def is_retrievable(self) -> bool:
        return self.status in RETRIEVABLE_STATUSES


class SourceDocument(BaseModel):
    """Loaded source text plus validated sidecar metadata."""

    model_config = ConfigDict(extra="forbid")

    metadata_path: Path
    content_path: Path
    raw_text: str
    computed_source_hash: HashValue
    metadata: DocumentMetadata

    @model_validator(mode="after")
    def validate_hash_match(self) -> SourceDocument:
        if self.computed_source_hash != self.metadata.source_hash:
            raise ValueError("computed source hash does not match metadata source_hash")
        return self

    @property
    def is_retrievable(self) -> bool:
        return self.metadata.is_retrievable


class DocumentChunk(BaseModel):
    """A deterministic source span that can be returned by retrieval."""

    model_config = ConfigDict(extra="forbid")

    chunk_id: NonBlankStr
    doc_id: NonBlankStr
    doc_title: NonBlankStr
    doc_type: DocumentType
    version: NonBlankStr
    status: DocumentStatus
    department: NonBlankStr
    section_heading: NonBlankStr
    source_file_path: Path
    source_hash: HashValue
    chunk_index: int = Field(ge=1)
    line_or_page_span: NonBlankStr
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    text: NonBlankStr

    @model_validator(mode="after")
    def validate_offsets(self) -> DocumentChunk:
        if self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self


class ValidationIssue(BaseModel):
    """One fail-closed corpus validation issue."""

    model_config = ConfigDict(extra="forbid")

    path: str
    message: str


class IngestReport(BaseModel):
    """Summary of one controlled-document corpus validation pass."""

    model_config = ConfigDict(extra="forbid")

    corpus_dir: Path
    metadata_files_seen: int = Field(ge=0)
    documents_valid: int = Field(ge=0)
    documents_retrievable: int = Field(ge=0)
    documents_excluded: int = Field(ge=0)
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.issues


class Corpus(BaseModel):
    """Validated corpus loaded from disk."""

    model_config = ConfigDict(extra="forbid")

    corpus_dir: Path
    documents: list[SourceDocument]
    report: IngestReport

    @property
    def retrievable_documents(self) -> list[SourceDocument]:
        return [document for document in self.documents if document.is_retrievable]


class RetrievalHit(BaseModel):
    """A ranked BM25 nomination over one retrievable chunk."""

    model_config = ConfigDict(extra="forbid")

    rank: int = Field(ge=1)
    score: float
    chunk: DocumentChunk

    def to_cli_record(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "score": self.score,
            "chunk_id": self.chunk.chunk_id,
            "doc_id": self.chunk.doc_id,
            "doc_title": self.chunk.doc_title,
            "status": self.chunk.status,
            "version": self.chunk.version,
            "section_heading": self.chunk.section_heading,
            "source_file_path": str(self.chunk.source_file_path),
            "source_hash": self.chunk.source_hash,
            "line_or_page_span": self.chunk.line_or_page_span,
            "text": self.chunk.text,
        }
