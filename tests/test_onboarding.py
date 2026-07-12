from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import load_corpus, validate_corpus
from biotech_rag_assistant.onboarding import OnboardingError, onboard_corpus
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
MESSY_CORPUS = ROOT / "examples/synthetic-messy-client-corpus"
EXPECTED_REPORT = MESSY_CORPUS / "expected/onboarding-report.json"
NORMALIZED_OUTPUT = Path("build/onboarded-synthetic-corpus")


def _report_records() -> dict[str, dict]:
    report = onboard_corpus(MESSY_CORPUS, output_dir=NORMALIZED_OUTPUT, force=True)
    return {record["source_path"]: record for record in report.to_cli_record()["records"]}


def test_onboarding_report_matches_committed_golden() -> None:
    report = onboard_corpus(MESSY_CORPUS, output_dir=NORMALIZED_OUTPUT, force=True)
    expected = json.loads(EXPECTED_REPORT.read_text(encoding="utf-8"))

    assert report.to_cli_record() == expected


def test_status_synonyms_map_through_metadata_map() -> None:
    records = _report_records()

    assert (
        records["incoming/documents/SOP-QA-001_v1.0_current-release.md"][
            "canonical_status"
        ]
        == "Effective"
    )
    assert (
        records["incoming/documents/POL-DOC-003_v2.0_approved.md"]["canonical_status"]
        == "Approved"
    )


def test_unknown_status_routes_to_review() -> None:
    record = _report_records()["incoming/documents/NOTE-TS-099_v1.0_unknown-status.md"]

    assert record["state"] == "needs_review"
    assert "unknown_status_value:In use pending QA" in record["reasons"]
    assert "canonical_status" not in record


def test_header_register_conflict_routes_to_review() -> None:
    record = _report_records()[
        "incoming/documents/DEV-QA-002_v1.0_conflicting-status.md"
    ]

    assert record["state"] == "needs_review"
    assert "conflicting_field_sources:status" in record["reasons"]
    assert "canonical_status" not in record


def test_missing_required_field_routes_to_review() -> None:
    record = _report_records()[
        "incoming/documents/SPEC-QC-006_v1.2_missing-effective-date.md"
    ]

    assert record["state"] == "needs_review"
    assert "missing_required_field:effective_date" in record["reasons"]
    assert "emitted_metadata_path" not in record


def test_duplicate_current_versions_route_to_review() -> None:
    records = _report_records()
    candidate_a = records["incoming/documents/SOP-OPS-007_v1.0_current-a.md"]
    candidate_b = records["incoming/documents/SOP-OPS-007_v1.1_current-b.md"]

    assert candidate_a["state"] == "needs_review"
    assert candidate_b["state"] == "needs_review"
    assert candidate_a["doc_id"] == "SOP-OPS-007"
    assert candidate_b["doc_id"] == "SOP-OPS-007"
    assert "duplicate_current_version" in candidate_a["reasons"]
    assert "duplicate_current_version" in candidate_b["reasons"]


def test_empty_source_routes_to_rejected() -> None:
    record = _report_records()["incoming/documents/empty-placeholder.md"]

    assert record["state"] == "rejected"
    assert "empty_source_text" in record["reasons"]
    assert record["doc_id"] == "EMP-QA-000"


def test_filename_derived_identity_is_recorded() -> None:
    record = _report_records()["incoming/documents/SOP-QA-001_v1.0_current-release.md"]

    assert record["doc_id"] == "SOP-QA-001"
    assert record["version"] == "1.0"
    assert record["field_sources"]["doc_id"] == "filename"
    assert record["field_sources"]["version"] == "filename"


def test_generated_sidecars_pass_existing_corpus_validator() -> None:
    report = onboard_corpus(MESSY_CORPUS, output_dir=NORMALIZED_OUTPUT, force=True)
    _documents, ingest_report = validate_corpus(NORMALIZED_OUTPUT)

    assert report.emitted_document_count == 4
    assert ingest_report.valid
    assert ingest_report.documents_valid == 4
    assert ingest_report.documents_retrievable == 2
    assert ingest_report.documents_excluded == 2


def test_retrieval_uses_only_clean_retrievable_records() -> None:
    onboard_corpus(MESSY_CORPUS, output_dir=NORMALIZED_OUTPUT, force=True)
    corpus = load_corpus(NORMALIZED_OUTPUT)
    chunks = chunk_documents(corpus.documents)
    indexed_doc_ids = {chunk.doc_id for chunk in chunks}

    assert indexed_doc_ids == {"POL-DOC-003", "SOP-QA-001"}
    assert {chunk.status for chunk in chunks} == {"Approved", "Effective"}

    green_hits = run_retrieval(
        corpus.documents,
        "viable excursions classified areas",
        RetrievalConfig(top_k=3),
    )
    assert green_hits
    assert green_hits[0].chunk.doc_id == "SOP-QA-001"

    blocked_hits = run_retrieval(
        corpus.documents,
        "superseded line clearance draft-only wording",
        RetrievalConfig(top_k=3),
    )
    assert blocked_hits == []


def test_unsafe_source_path_is_rejected(tmp_path: Path) -> None:
    messy = tmp_path / "messy"
    incoming = messy / "incoming/documents"
    incoming.mkdir(parents=True)
    (messy / "metadata-map.yaml").write_text(
        (MESSY_CORPUS / "metadata-map.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (messy / "incoming/source-register.yaml").write_text(
        yaml.safe_dump(
            {
                "records": [
                    {
                        "source_path": "../outside.md",
                        "doc_id": "BAD-QA-001",
                        "doc_title": "Unsafe path",
                        "doc_type": "SOP",
                        "version": "1.0",
                        "status": "Released",
                        "effective_date": "2026-01-01",
                        "department": "QA",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    report = onboard_corpus(messy, output_dir=tmp_path / "out")
    record = report.to_cli_record()["records"][0]

    assert record["state"] == "rejected"
    assert "unsafe_source_path" in record["reasons"]


def test_onboard_refuses_to_overwrite_nonempty_output_without_force(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "preexisting.txt").write_text("keep me", encoding="utf-8")

    with pytest.raises(OnboardingError):
        onboard_corpus(MESSY_CORPUS, output_dir=out)

    # The pre-existing data is left untouched when the run refuses.
    assert (out / "preexisting.txt").read_text(encoding="utf-8") == "keep me"


def test_onboard_overwrites_nonempty_output_with_force(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / "stale.txt").write_text("old", encoding="utf-8")

    report = onboard_corpus(MESSY_CORPUS, output_dir=out, force=True)

    assert report.emitted_document_count > 0
    assert not (out / "stale.txt").exists()
    _documents, ingest = validate_corpus(out)
    assert ingest.valid
