from __future__ import annotations

from pathlib import Path

import yaml

from biotech_rag_assistant.chunking import chunk_documents
from biotech_rag_assistant.corpus import compute_source_hash, load_corpus, validate_corpus

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"


def _write_doc(
    corpus_dir: Path,
    name: str,
    doc_id: str,
    version: str,
    status: str,
    body: str,
) -> None:
    documents = corpus_dir / "documents"
    metadata = corpus_dir / "metadata"
    documents.mkdir(parents=True, exist_ok=True)
    metadata.mkdir(parents=True, exist_ok=True)
    content_path = documents / f"{name}.md"
    content_path.write_text(body, encoding="utf-8")
    (metadata / f"{name}.yaml").write_text(
        yaml.safe_dump(
            {
                "doc_id": doc_id,
                "doc_title": f"{doc_id} {version}",
                "doc_type": "SOP",
                "version": version,
                "status": status,
                "effective_date": "2026-01-15",
                "department": "QA",
                "source_file_path": f"documents/{name}.md",
                "source_hash": compute_source_hash(content_path),
            }
        ),
        encoding="utf-8",
    )


def test_demo_corpus_validates_cleanly() -> None:
    documents, report = validate_corpus(DEMO_CORPUS)

    assert report.valid
    assert report.metadata_files_seen == 10
    assert report.documents_valid == 10
    assert report.documents_retrievable == 8
    assert report.documents_excluded == 2
    assert len(documents) == 10


def test_missing_status_fails_closed() -> None:
    fixture = ROOT / "tests/fixtures/missing-status"
    _documents, report = validate_corpus(fixture)

    assert not report.valid
    assert any("status" in issue.message for issue in report.issues)


def test_duplicate_current_version_fails_closed(tmp_path: Path) -> None:
    # Two Approved versions of the same doc_id make 'current approved' ambiguous (ADR-013).
    _write_doc(tmp_path, "sop-a-v1", "SOP-QA-100", "1.0", "Approved", "# A\n\nBody one.\n")
    _write_doc(tmp_path, "sop-a-v2", "SOP-QA-100", "2.0", "Approved", "# A\n\nBody two.\n")

    _documents, report = validate_corpus(tmp_path)

    assert not report.valid
    assert any("more than one retrievable version" in issue.message for issue in report.issues)


def test_single_current_version_with_superseded_validates(tmp_path: Path) -> None:
    # The normal case: one Approved version plus a Superseded predecessor is allowed,
    # because only the Approved version is retrievable.
    _write_doc(tmp_path, "sop-b-v1", "SOP-QA-101", "1.0", "Superseded", "# B\n\nOld.\n")
    _write_doc(tmp_path, "sop-b-v2", "SOP-QA-101", "2.0", "Approved", "# B\n\nNew.\n")

    _documents, report = validate_corpus(tmp_path)

    assert report.valid
    assert report.documents_retrievable == 1


def test_draft_and_obsolete_documents_do_not_enter_chunks() -> None:
    corpus = load_corpus(DEMO_CORPUS)
    chunks = chunk_documents(corpus.documents)

    indexed_doc_ids = {chunk.doc_id for chunk in chunks}

    assert "SOP-QA-009" not in indexed_doc_ids
    assert "SOP-QA-010" not in indexed_doc_ids
    assert "SOP-QA-001" in indexed_doc_ids
