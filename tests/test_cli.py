from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from biotech_rag_assistant.cli import cli

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
MESSY_CORPUS = ROOT / "examples/synthetic-messy-client-corpus"
EXPECTED_ONBOARDING_REPORT = MESSY_CORPUS / "expected/onboarding-report.json"


def test_validate_corpus_cli_passes_for_demo_corpus() -> None:
    result = CliRunner().invoke(cli, ["validate-corpus", str(DEMO_CORPUS)])

    assert result.exit_code == 0
    assert "Corpus validation passed" in result.output
    assert "Documents retrievable: 8" in result.output


def test_onboard_corpus_cli_writes_reports_and_json() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "onboard-corpus",
            str(MESSY_CORPUS),
            "--output",
            "build/onboarded-synthetic-corpus",
            "--report-out",
            "build/onboarding-report.json",
            "--markdown-out",
            "build/onboarding-report.md",
            "--force",
            "--json",
        ],
    )

    assert result.exit_code == 0, result.output
    expected = json.loads(EXPECTED_ONBOARDING_REPORT.read_text(encoding="utf-8"))
    assert json.loads(result.output) == expected
    assert json.loads(Path("build/onboarding-report.json").read_text("utf-8")) == expected
    assert "retrieval nominates candidate passages" in Path(
        "build/onboarding-report.md"
    ).read_text("utf-8")


def test_onboard_corpus_cli_dry_run_skips_normalized_output(tmp_path: Path) -> None:
    output_dir = tmp_path / "dry-run-normalized"
    result = CliRunner().invoke(
        cli,
        [
            "onboard-corpus",
            str(MESSY_CORPUS),
            "--output",
            str(output_dir),
            "--report-out",
            str(tmp_path / "report.json"),
            "--dry-run",
        ],
    )

    assert result.exit_code == 0, result.output
    assert not output_dir.exists()
    assert (tmp_path / "report.json").exists()


def test_onboard_corpus_cli_require_no_review_fails_after_report(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    result = CliRunner().invoke(
        cli,
        [
            "onboard-corpus",
            str(MESSY_CORPUS),
            "--output",
            str(tmp_path / "normalized"),
            "--report-out",
            str(report_path),
            "--require-no-review",
        ],
    )

    assert result.exit_code != 0
    assert report_path.exists()
    assert "onboarding produced review or rejection records" in result.output


def test_retrieve_cli_json_includes_traceable_fields() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "retrieve",
            str(DEMO_CORPUS),
            "--query",
            "viable excursion affected product lots immediate containment",
            "--top-k",
            "1",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    hit = payload["hits"][0]

    assert hit["chunk_id"] == "SOP-QA-001_v1_0_chunk_002"
    assert hit["doc_id"] == "SOP-QA-001"
    assert hit["source_hash"].startswith("sha256:")
    assert hit["status"] == "Approved"


def test_retrieve_cli_reports_no_hits_without_error() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "retrieve",
            str(DEMO_CORPUS),
            "--query",
            "zzzz qqqq impossible-token",
        ],
    )

    assert result.exit_code == 0
    assert "No retrievable chunks matched the query." in result.output


def test_answer_cli_returns_validated_extractive_answer() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "answer",
            str(DEMO_CORPUS),
            "--query",
            "viable excursion affected product lots immediate containment",
            "--top-k",
            "1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["outcome"] == "answer"
    assert payload["citations"][0]["chunk_id"] == "SOP-QA-001_v1_0_chunk_002"
    assert payload["citation_validation"]["valid"] is True
    assert "[source: 1]" in payload["answer_text"]


def test_answer_cli_refuses_without_hits() -> None:
    result = CliRunner().invoke(
        cli,
        [
            "answer",
            str(DEMO_CORPUS),
            "--query",
            "zzzz qqqq impossible-token",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["outcome"] == "refusal"
    assert payload["citations"] == []
    assert payload["retrieved_chunks"] == []


def test_validate_citations_cli_passes_for_valid_fixture() -> None:
    fixture_dir = ROOT / "tests/fixtures/citation-validation"
    result = CliRunner().invoke(
        cli,
        [
            "validate-citations",
            str(fixture_dir / "retrieval-valid.json"),
            str(fixture_dir / "answer-valid.json"),
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["valid"] is True
    assert payload["metric_name"] == "citation_resolves_to_retrieved_chunk"


def test_validate_citations_cli_fails_for_hallucinated_chunk() -> None:
    fixture_dir = ROOT / "tests/fixtures/citation-validation"
    result = CliRunner().invoke(
        cli,
        [
            "validate-citations",
            str(fixture_dir / "retrieval-valid.json"),
            str(fixture_dir / "answer-hallucinated-citation.json"),
        ],
    )

    assert result.exit_code != 0
    assert "unresolved_citation" in result.output
    assert "citation validation failed" in result.output


def test_evaluate_cli_writes_reports(tmp_path: Path) -> None:
    json_out = tmp_path / "evaluation-report.json"
    markdown_out = tmp_path / "evaluation-report.md"
    result = CliRunner().invoke(
        cli,
        [
            "evaluate",
            str(DEMO_CORPUS),
            str(DEMO_CORPUS / "evaluation/golden-questions.json"),
            "--json-out",
            str(json_out),
            "--markdown-out",
            str(markdown_out),
        ],
    )

    assert result.exit_code == 0
    assert "Trust layer status: pass" in result.output
    assert "case_pass_rate: 24/24" in result.output
    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["trust_layer_status"] == "pass"
    assert "does not measure semantic support" in markdown_out.read_text(
        encoding="utf-8"
    )
