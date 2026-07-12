"""Client-corpus onboarding before controlled-document ingest.

The onboarding layer maps a messy source bundle into the existing clean corpus
contract. It does not change retrieval behavior. Only records that can be emitted as
``DocumentMetadata`` sidecars reach ``validate_corpus``.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from biotech_rag_assistant.corpus import compute_source_hash
from biotech_rag_assistant.models import DocumentMetadata, DocumentStatus, DocumentType

OnboardingState = Literal["mapped_cleanly", "excluded", "needs_review", "rejected"]

RETRIEVABLE_STATUSES = {"Approved", "Effective"}
NON_RETRIEVABLE_STATUSES = {"Draft", "Obsolete", "Superseded"}
REPORT_TYPE = "client_corpus_onboarding"
REPORT_SCHEMA_VERSION = "0.1.0"
REQUIRED_FIELD_ORDER = [
    "doc_id",
    "doc_title",
    "doc_type",
    "version",
    "status",
    "effective_date",
    "department",
]


class OnboardingError(Exception):
    """Raised when onboarding inputs are unreadable or structurally invalid."""


class FilenamePattern(BaseModel):
    """Configured filename regex for deterministic field extraction."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    pattern: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_pattern(self) -> FilenamePattern:
        try:
            re.compile(self.pattern)
        except re.error as exc:
            raise ValueError(f"invalid filename pattern: {exc}") from exc
        return self


class MappingConfig(BaseModel):
    """Versioned per-client mapping from local conventions to clean metadata."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(min_length=1)
    client_label: str = Field(min_length=1)
    status_map: dict[str, DocumentStatus]
    doc_type_map: dict[str, DocumentType]
    filename_patterns: list[FilenamePattern] = Field(default_factory=list)
    header_fields: dict[str, str] = Field(default_factory=dict)
    required_fields: list[str] = Field(default_factory=lambda: list(REQUIRED_FIELD_ORDER))


class SourceRegisterRecord(BaseModel):
    """One optional source-system register row for a messy document."""

    model_config = ConfigDict(extra="forbid")

    source_path: str = Field(min_length=1)
    doc_id: str | None = None
    doc_title: str | None = None
    doc_type: str | None = None
    version: str | None = None
    status: str | None = None
    effective_date: str | None = None
    department: str | None = None
    current_version: bool | None = None


class SourceRegister(BaseModel):
    """Loaded source-register file."""

    model_config = ConfigDict(extra="forbid")

    records: list[SourceRegisterRecord]


class FieldCoverage(BaseModel):
    """Established/missing counts for one clean metadata field."""

    model_config = ConfigDict(extra="forbid")

    established: int = Field(ge=0)
    missing: int = Field(ge=0)


class OnboardingRecord(BaseModel):
    """One document-level onboarding outcome."""

    model_config = ConfigDict(extra="forbid")

    source_path: str
    state: OnboardingState
    retrievable: bool
    reasons: list[str] = Field(default_factory=list)
    field_sources: dict[str, str] = Field(default_factory=dict)
    doc_id: str | None = None
    doc_title: str | None = None
    doc_type: DocumentType | None = None
    version: str | None = None
    canonical_status: DocumentStatus | None = None
    effective_date: str | None = None
    department: str | None = None
    emitted_metadata_path: str | None = None


class OnboardingReport(BaseModel):
    """Deterministic coverage report for one onboarding pass."""

    model_config = ConfigDict(extra="forbid")

    report_type: Literal["client_corpus_onboarding"] = REPORT_TYPE
    schema_version: Literal["0.1.0"] = REPORT_SCHEMA_VERSION
    source_bundle: str
    mapping_config_hash: str
    source_register_hash: str
    input_document_count: int = Field(ge=0)
    emitted_document_count: int = Field(ge=0)
    state_counts: dict[OnboardingState, int]
    field_coverage: dict[str, FieldCoverage]
    canonical_status_counts: dict[DocumentStatus, int]
    unknown_status_values: list[str] = Field(default_factory=list)
    normalized_corpus_dir: str | None = None
    records: list[OnboardingRecord]

    def to_cli_record(self) -> dict[str, object]:
        """Return deterministic JSON-ready report data."""
        return self.model_dump(mode="json", exclude_none=True)


def load_mapping_config(path: Path) -> MappingConfig:
    """Load and validate onboarding mapping YAML."""
    raw = _load_yaml_mapping(path, "mapping config")
    try:
        return MappingConfig.model_validate(raw)
    except ValidationError as exc:
        raise OnboardingError(_format_validation_error(path, exc)) from exc


def load_source_register(path: Path) -> SourceRegister:
    """Load and validate source register YAML."""
    raw = _load_yaml_mapping(path, "source register")
    records_raw = raw.get("records") if isinstance(raw, dict) else raw
    if records_raw is None:
        raise OnboardingError(f"{path}: source register must contain records")
    try:
        return SourceRegister.model_validate({"records": records_raw})
    except ValidationError as exc:
        raise OnboardingError(_format_validation_error(path, exc)) from exc


def onboard_corpus(
    messy_corpus_dir: Path,
    *,
    output_dir: Path | None,
    mapping_path: Path | None = None,
    register_path: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> OnboardingReport:
    """Map a messy corpus into the existing clean corpus shape."""
    messy_corpus_dir = messy_corpus_dir.resolve()
    mapping_path = mapping_path or messy_corpus_dir / "metadata-map.yaml"
    register_path = register_path or messy_corpus_dir / "incoming/source-register.yaml"
    mapping = load_mapping_config(mapping_path)
    register = load_source_register(register_path)
    register_by_source = {record.source_path: record for record in register.records}
    records = [
        _evaluate_source(
            messy_corpus_dir=messy_corpus_dir,
            source_path=source_path,
            mapping=mapping,
            register_record=register_by_source.get(source_path),
        )
        for source_path in _source_paths(messy_corpus_dir, register)
    ]

    records = _apply_duplicate_current_review(records, register_by_source)
    emitted_records: list[OnboardingRecord] = []
    normalized_dir: str | None = str(output_dir) if output_dir is not None else None
    if output_dir is not None and not dry_run:
        emitted_records = _write_normalized_corpus(
            messy_corpus_dir,
            output_dir,
            records,
            force=force,
        )
        record_by_source = {record.source_path: record for record in emitted_records}
        records = [record_by_source.get(record.source_path, record) for record in records]
    else:
        emitted_records = [record for record in records if _should_emit(record)]

    return OnboardingReport(
        source_bundle=messy_corpus_dir.name,
        mapping_config_hash=compute_source_hash(mapping_path),
        source_register_hash=compute_source_hash(register_path),
        input_document_count=len(records),
        emitted_document_count=len(emitted_records),
        state_counts=_state_counts(records),
        field_coverage=_field_coverage(records),
        canonical_status_counts=_status_counts(records),
        unknown_status_values=sorted(_unknown_status_values(records)),
        normalized_corpus_dir=normalized_dir,
        records=records,
    )


def render_markdown_report(report: OnboardingReport) -> str:
    """Render a compact human-readable onboarding report."""
    lines = [
        "# Biotech RAG client-corpus onboarding report",
        "",
        "This report measures whether synthetic client documents can be mapped into "
        "the clean controlled-document corpus contract before retrieval. The report "
        "states that retrieval nominates candidate passages. It does not certify truth "
        "or compliance.",
        "",
        "## Summary",
        "",
        f"- Source bundle: `{report.source_bundle}`",
        f"- Input documents: {report.input_document_count}",
        f"- Emitted documents: {report.emitted_document_count}",
        f"- Normalized corpus: `{report.normalized_corpus_dir or 'n/a'}`",
        "",
        "## State counts",
        "",
    ]
    for state, count in report.state_counts.items():
        lines.append(f"- `{state}`: {count}")

    lines.extend(["", "## Field coverage", ""])
    for field, coverage in report.field_coverage.items():
        lines.append(
            f"- `{field}`: {coverage.established} established, {coverage.missing} missing"
        )

    lines.extend(["", "## Unknown status values", ""])
    if report.unknown_status_values:
        for value in report.unknown_status_values:
            lines.append(f"- `{value}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Records needing review", ""])
    _append_records_by_state(lines, report.records, "needs_review")

    lines.extend(["", "## Rejected records", ""])
    _append_records_by_state(lines, report.records, "rejected")
    lines.append("")
    return "\n".join(lines)


def write_json_report(report: OnboardingReport, path: Path) -> None:
    """Write deterministic report JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_cli_record(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(report: OnboardingReport, path: Path) -> None:
    """Write Markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")


def _evaluate_source(
    *,
    messy_corpus_dir: Path,
    source_path: str,
    mapping: MappingConfig,
    register_record: SourceRegisterRecord | None,
) -> OnboardingRecord:
    absolute_source = (messy_corpus_dir / source_path).resolve()
    reasons: list[str] = []
    if not _is_inside(absolute_source, messy_corpus_dir / "incoming/documents"):
        return OnboardingRecord(
            source_path=source_path,
            state="rejected",
            retrievable=False,
            reasons=["unsafe_source_path"],
        )

    header_values: dict[str, str] = {}
    raw_text = ""
    if absolute_source.exists() and absolute_source.is_file():
        raw_text = absolute_source.read_text(encoding="utf-8")
        header_values = _extract_header_values(raw_text, mapping.header_fields)
    else:
        reasons.append("source_file_not_found")

    filename_values = _extract_filename_values(Path(source_path).name, mapping)
    fields: dict[str, str] = {}
    field_sources: dict[str, str] = {}

    for field in REQUIRED_FIELD_ORDER:
        values = _candidate_values(field, register_record, filename_values, header_values)
        established = _establish_field(field, values, mapping, reasons, source_path)
        if established is not None:
            value, source = established
            fields[field] = value
            field_sources[field] = source

    if not raw_text.strip():
        reasons.append("empty_source_text")

    missing_required = [
        field for field in mapping.required_fields if field not in fields
    ]
    for field in missing_required:
        if not any(reason.startswith(f"missing_required_field:{field}") for reason in reasons):
            reasons.append(f"missing_required_field:{field}")

    canonical_status = fields.get("status")
    state = _record_state(canonical_status, reasons)
    return OnboardingRecord(
        source_path=source_path,
        state=state,
        retrievable=canonical_status in RETRIEVABLE_STATUSES and state == "mapped_cleanly",
        reasons=sorted(set(reasons)),
        field_sources=field_sources,
        doc_id=fields.get("doc_id"),
        doc_title=fields.get("doc_title"),
        doc_type=fields.get("doc_type"),  # type: ignore[arg-type]
        version=fields.get("version"),
        canonical_status=canonical_status,  # type: ignore[arg-type]
        effective_date=fields.get("effective_date"),
        department=fields.get("department"),
    )


def _apply_duplicate_current_review(
    records: list[OnboardingRecord],
    register_by_source: dict[str, SourceRegisterRecord],
) -> list[OnboardingRecord]:
    retrievable_by_doc_id: dict[str, list[OnboardingRecord]] = {}
    for record in records:
        if record.doc_id and record.canonical_status in RETRIEVABLE_STATUSES:
            retrievable_by_doc_id.setdefault(record.doc_id, []).append(record)

    duplicate_sources: set[str] = set()
    for doc_records in retrievable_by_doc_id.values():
        if len(doc_records) <= 1:
            continue
        current_records = [
            record
            for record in doc_records
            if register_by_source.get(record.source_path)
            and register_by_source[record.source_path].current_version is True
        ]
        if len(current_records) != 1:
            duplicate_sources.update(record.source_path for record in doc_records)

    updated: list[OnboardingRecord] = []
    for record in records:
        if record.source_path not in duplicate_sources:
            updated.append(record)
            continue
        reasons = sorted(set([*record.reasons, "duplicate_current_version"]))
        updated.append(
            record.model_copy(
                update={
                    "state": "needs_review",
                    "retrievable": False,
                    "reasons": reasons,
                }
            )
        )
    return updated


def _write_normalized_corpus(
    messy_corpus_dir: Path,
    output_dir: Path,
    records: list[OnboardingRecord],
    *,
    force: bool = False,
) -> list[OnboardingRecord]:
    output_dir = output_dir.resolve()
    # Never clobber existing data by default: this tool handles client documents, so refuse to
    # overwrite a non-empty output directory unless the caller explicitly opts in with force.
    if output_dir.exists() and any(output_dir.iterdir()):
        if not force:
            raise OnboardingError(
                f"output directory {output_dir} already exists and is not empty; refusing to "
                "overwrite it. Pass force=True (CLI: --force) to replace its contents."
            )
        shutil.rmtree(output_dir)
    documents_dir = output_dir / "documents"
    metadata_dir = output_dir / "metadata"
    documents_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)

    emitted: list[OnboardingRecord] = []
    for record in records:
        if not _should_emit(record):
            continue
        source = (messy_corpus_dir / record.source_path).resolve()
        output_document = documents_dir / source.name
        shutil.copyfile(source, output_document)
        sidecar = _metadata_for_record(record, output_document, output_dir)
        metadata_filename = f"{Path(record.source_path).stem}.yaml"
        metadata_path = metadata_dir / metadata_filename
        metadata_path.write_text(
            yaml.safe_dump(sidecar.model_dump(mode="json"), sort_keys=False),
            encoding="utf-8",
        )
        emitted.append(
            record.model_copy(
                update={"emitted_metadata_path": f"metadata/{metadata_filename}"}
            )
        )
    return emitted


def _metadata_for_record(
    record: OnboardingRecord,
    output_document: Path,
    output_dir: Path,
) -> DocumentMetadata:
    relative_path = output_document.relative_to(output_dir)
    payload = {
        "doc_id": record.doc_id,
        "doc_title": record.doc_title,
        "doc_type": record.doc_type,
        "version": record.version,
        "status": record.canonical_status,
        "effective_date": record.effective_date,
        "department": record.department,
        "source_file_path": relative_path,
        "source_hash": compute_source_hash(output_document),
    }
    return DocumentMetadata.model_validate(payload)


def _should_emit(record: OnboardingRecord) -> bool:
    return record.state in {"mapped_cleanly", "excluded"}


def _record_state(status: str | None, reasons: list[str]) -> OnboardingState:
    if "empty_source_text" in reasons or "unsafe_source_path" in reasons:
        return "rejected"
    if "no_establishable_doc_id" in reasons:
        return "rejected"
    if any(reason.startswith("source_file_not_found") for reason in reasons):
        return "rejected"
    if reasons:
        return "needs_review"
    if status in RETRIEVABLE_STATUSES:
        return "mapped_cleanly"
    if status in NON_RETRIEVABLE_STATUSES:
        return "excluded"
    return "needs_review"


def _candidate_values(
    field: str,
    register_record: SourceRegisterRecord | None,
    filename_values: dict[str, str],
    header_values: dict[str, str],
) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if register_record is not None:
        value = getattr(register_record, field, None)
        if value:
            values.append(("register", str(value).strip()))
    if field in filename_values:
        values.append(("filename", filename_values[field]))
    if field in header_values:
        values.append(("header", header_values[field]))
    return values


def _establish_field(
    field: str,
    values: list[tuple[str, str]],
    mapping: MappingConfig,
    reasons: list[str],
    source_path: str,
) -> tuple[str, str] | None:
    normalized: list[tuple[str, str]] = []
    for source, value in values:
        mapped = _normalize_field_value(field, value, mapping, reasons)
        if mapped is not None:
            normalized.append((source, mapped))

    if not normalized:
        if field == "doc_id":
            reasons.append("no_establishable_doc_id")
        return None

    unique_values = {value for _source, value in normalized}
    if len(unique_values) > 1:
        reasons.append(f"conflicting_field_sources:{field}")
        return None

    if field == "version":
        return normalized[-1][1], normalized[-1][0]
    return normalized[0][1], normalized[0][0]


def _normalize_field_value(
    field: str,
    value: str,
    mapping: MappingConfig,
    reasons: list[str],
) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    if field == "status":
        mapped = mapping.status_map.get(stripped)
        if mapped is None:
            reasons.append(f"unknown_status_value:{stripped}")
            return None
        return mapped
    if field == "doc_type":
        mapped = mapping.doc_type_map.get(stripped)
        if mapped is None:
            reasons.append(f"unsupported_doc_type:{stripped}")
            return None
        return mapped
    if field == "version":
        return _normalize_version(stripped)
    return stripped


def _extract_filename_values(filename: str, mapping: MappingConfig) -> dict[str, str]:
    for pattern in mapping.filename_patterns:
        match = re.search(pattern.pattern, filename)
        if match:
            values = {
                key: value
                for key, value in match.groupdict().items()
                if value is not None
            }
            if "version" in values:
                values["version"] = _normalize_version(values["version"])
            return values
    return {}


def _extract_header_values(text: str, header_fields: dict[str, str]) -> dict[str, str]:
    reverse = {header_name.lower(): field for field, header_name in header_fields.items()}
    values: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            break
        key, separator, value = line.partition(":")
        if not separator:
            break
        field = reverse.get(key.strip().lower())
        if field is not None:
            values[field] = value.strip()
    return values


def _normalize_version(value: str) -> str:
    stripped = value.strip()
    lowered = stripped.lower()
    if lowered.startswith("rev-"):
        return stripped[4:]
    if lowered.startswith("v") and len(stripped) > 1 and stripped[1].isdigit():
        return stripped[1:]
    return stripped


def _source_paths(messy_corpus_dir: Path, register: SourceRegister) -> list[str]:
    paths = {
        str(path.relative_to(messy_corpus_dir))
        for path in (messy_corpus_dir / "incoming/documents").glob("*.md")
    }
    paths.update(record.source_path for record in register.records)
    return sorted(paths)


def _state_counts(records: list[OnboardingRecord]) -> dict[OnboardingState, int]:
    return {
        "mapped_cleanly": sum(1 for record in records if record.state == "mapped_cleanly"),
        "excluded": sum(1 for record in records if record.state == "excluded"),
        "needs_review": sum(1 for record in records if record.state == "needs_review"),
        "rejected": sum(1 for record in records if record.state == "rejected"),
    }


def _field_coverage(records: list[OnboardingRecord]) -> dict[str, FieldCoverage]:
    coverage: dict[str, FieldCoverage] = {}
    for field in REQUIRED_FIELD_ORDER:
        established = sum(
            1 for record in records if getattr(record, _record_attr(field)) is not None
        )
        coverage[field] = FieldCoverage(
            established=established,
            missing=len(records) - established,
        )
    return coverage


def _record_attr(field: str) -> str:
    if field == "status":
        return "canonical_status"
    return field


def _status_counts(records: list[OnboardingRecord]) -> dict[DocumentStatus, int]:
    counts: dict[DocumentStatus, int] = {}
    for record in records:
        if record.canonical_status is not None:
            counts[record.canonical_status] = counts.get(record.canonical_status, 0) + 1
    return dict(sorted(counts.items()))


def _unknown_status_values(records: list[OnboardingRecord]) -> set[str]:
    values = set()
    for record in records:
        for reason in record.reasons:
            if reason.startswith("unknown_status_value:"):
                values.add(reason.split(":", 1)[1])
    return values


def _append_records_by_state(
    lines: list[str],
    records: list[OnboardingRecord],
    state: OnboardingState,
) -> None:
    matching = [record for record in records if record.state == state]
    if not matching:
        lines.append("- none")
        return
    for record in matching:
        reasons = ", ".join(record.reasons) if record.reasons else "none"
        lines.append(f"- `{record.source_path}`: {reasons}")


def _load_yaml_mapping(path: Path, label: str) -> object:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise OnboardingError(f"could not read {label} {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise OnboardingError(f"invalid YAML in {path}: {exc}") from exc
    if raw is None:
        raw = {}
    if not isinstance(raw, dict | list):
        raise OnboardingError(f"{path}: {label} must contain a mapping or list")
    return raw


def _format_validation_error(path: Path, exc: ValidationError) -> str:
    messages = []
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"])
        messages.append(f"{field}: {error['msg']}")
    return f"{path}: {'; '.join(messages)}"


def _is_inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True
