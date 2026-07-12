"""Load and validate controlled-document corpora."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from pathlib import Path

import yaml
from pydantic import ValidationError

from biotech_rag_assistant.models import (
    Corpus,
    DocumentMetadata,
    IngestReport,
    SourceDocument,
    ValidationIssue,
)


class CorpusValidationError(Exception):
    """Raised when a corpus has fail-closed validation issues."""

    def __init__(self, report: IngestReport) -> None:
        self.report = report
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in report.issues)
        super().__init__(details or "corpus validation failed")


def compute_source_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def validate_corpus(corpus_dir: Path) -> tuple[list[SourceDocument], IngestReport]:
    """Validate sidecars and source hashes without silently indexing bad records."""
    corpus_dir = corpus_dir.resolve()
    metadata_dir = corpus_dir / "metadata"
    issues: list[ValidationIssue] = []
    documents: list[SourceDocument] = []

    if not metadata_dir.exists():
        issues.append(
            ValidationIssue(
                path=str(metadata_dir),
                message="metadata directory is required",
            )
        )
        return documents, _report(corpus_dir, 0, documents, issues)

    metadata_paths = sorted(metadata_dir.glob("*.yaml"))
    if not metadata_paths:
        issues.append(
            ValidationIssue(
                path=str(metadata_dir),
                message="at least one metadata YAML sidecar is required",
            )
        )

    for metadata_path in metadata_paths:
        metadata = _load_metadata(metadata_path, corpus_dir, issues)
        if metadata is None:
            continue

        content_path = (corpus_dir / metadata.source_file_path).resolve()
        if not _is_inside(content_path, corpus_dir):
            issues.append(
                ValidationIssue(
                    path=str(metadata_path.relative_to(corpus_dir)),
                    message="source_file_path must stay inside the corpus directory",
                )
            )
            continue
        if not content_path.exists() or not content_path.is_file():
            issues.append(
                ValidationIssue(
                    path=str(metadata_path.relative_to(corpus_dir)),
                    message=f"source file not found: {metadata.source_file_path}",
                )
            )
            continue

        computed_hash = compute_source_hash(content_path)
        if computed_hash != metadata.source_hash:
            issues.append(
                ValidationIssue(
                    path=str(metadata_path.relative_to(corpus_dir)),
                    message="source_hash does not match source file content",
                )
            )
            continue

        raw_text = content_path.read_text(encoding="utf-8")
        if not raw_text.strip():
            issues.append(
                ValidationIssue(
                    path=str(metadata.source_file_path),
                    message="source file must not be empty",
                )
            )
            continue

        documents.append(
            SourceDocument(
                metadata_path=metadata_path,
                content_path=content_path,
                raw_text=raw_text,
                computed_source_hash=computed_hash,
                metadata=metadata,
            )
        )

    _flag_duplicate_current_versions(documents, issues)

    return documents, _report(corpus_dir, len(metadata_paths), documents, issues)


def load_corpus(corpus_dir: Path) -> Corpus:
    """Load a corpus or raise a fail-closed validation error."""
    documents, report = validate_corpus(corpus_dir)
    if not report.valid:
        raise CorpusValidationError(report)
    return Corpus(corpus_dir=corpus_dir.resolve(), documents=documents, report=report)


def _load_metadata(
    metadata_path: Path,
    corpus_dir: Path,
    issues: list[ValidationIssue],
) -> DocumentMetadata | None:
    try:
        raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        issues.append(
            ValidationIssue(
                path=str(metadata_path.relative_to(corpus_dir)),
                message=f"invalid YAML: {exc}",
            )
        )
        return None

    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        issues.append(
            ValidationIssue(
                path=str(metadata_path.relative_to(corpus_dir)),
                message="metadata sidecar must contain a mapping",
            )
        )
        return None

    try:
        return DocumentMetadata.model_validate(raw)
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            messages.append(f"{field}: {error['msg']}")
        issues.append(
            ValidationIssue(
                path=str(metadata_path.relative_to(corpus_dir)),
                message="; ".join(messages),
            )
        )
        return None


def _report(
    corpus_dir: Path,
    metadata_files_seen: int,
    documents: list[SourceDocument],
    issues: list[ValidationIssue],
) -> IngestReport:
    retrievable = [document for document in documents if document.is_retrievable]
    excluded = [document for document in documents if not document.is_retrievable]
    return IngestReport(
        corpus_dir=corpus_dir,
        metadata_files_seen=metadata_files_seen,
        documents_valid=len(documents),
        documents_retrievable=len(retrievable),
        documents_excluded=len(excluded),
        issues=issues,
    )


def _flag_duplicate_current_versions(
    documents: list[SourceDocument],
    issues: list[ValidationIssue],
) -> None:
    """Fail closed when a doc_id has more than one retrievable version (ADR-013).

    The product's core use case is 'show me the current approved version'. The status
    gate excludes Draft/Obsolete/Superseded, but two Approved/Effective versions of the
    same doc_id would both validate and both retrieve, making 'current' ambiguous. A
    fail-closed corpus must not leave that to authoring discipline.
    """
    by_doc_id: dict[str, list[SourceDocument]] = defaultdict(list)
    for document in documents:
        if document.is_retrievable:
            by_doc_id[document.metadata.doc_id].append(document)

    for doc_id, retrievable in sorted(by_doc_id.items()):
        if len(retrievable) > 1:
            versions = ", ".join(sorted(document.metadata.version for document in retrievable))
            issues.append(
                ValidationIssue(
                    path=doc_id,
                    message=(
                        f"more than one retrievable version for doc_id '{doc_id}' "
                        f"(versions: {versions}); exactly one Approved/Effective version "
                        "may be retrievable"
                    ),
                )
            )


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True
