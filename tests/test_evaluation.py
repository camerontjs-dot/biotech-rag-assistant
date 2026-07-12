from __future__ import annotations

import json
from pathlib import Path

from biotech_rag_assistant.evaluation import (
    load_evaluation_suite,
    render_markdown_report,
    run_evaluation_suite,
    write_json_report,
    write_markdown_report,
)

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
SUITE_PATH = DEMO_CORPUS / "evaluation/golden-questions.json"
NL_SUITE_PATH = DEMO_CORPUS / "evaluation/natural-language-queries.json"


def test_trust_layer_evaluation_suite_passes_expected_traps() -> None:
    report = run_evaluation_suite(DEMO_CORPUS, load_evaluation_suite(SUITE_PATH))

    assert report.valid
    assert report.trust_layer_status == "pass"
    assert report.case_count == 24
    assert report.metrics["case_pass_rate"] == "24/24"
    assert report.metrics["citation_expectation_match_rate"] == "6/6"
    assert report.metrics["generated_answer_citation_validation_rate"] == "24/24"


def test_natural_language_suite_answers_on_topic_and_refuses_off_topic() -> None:
    # Realistic conversational queries kept separate from the trap suite (ADR-012):
    # on-topic questions answer; out-of-domain questions refuse via the relevance gate.
    report = run_evaluation_suite(DEMO_CORPUS, load_evaluation_suite(NL_SUITE_PATH))

    assert report.valid
    assert report.trust_layer_status == "pass"
    assert report.case_count == 13
    assert report.metrics["retrieval_expectation_match_rate"] == "13/13"
    assert report.metrics["refusal_expectation_match_rate"] == "6/6"


def test_evaluation_report_keeps_structural_citation_limit_visible() -> None:
    report = run_evaluation_suite(DEMO_CORPUS, load_evaluation_suite(SUITE_PATH))

    markdown = render_markdown_report(report)

    assert "`citation_resolves_to_retrieved_chunk` means a cited `chunk_id` appeared" in markdown
    assert "It does not measure semantic support." in markdown
    assert "## Corpus/config" in markdown
    assert "## Case table" in markdown
    assert "## Limits" in markdown


def test_evaluation_report_writes_json_and_markdown(tmp_path: Path) -> None:
    report = run_evaluation_suite(DEMO_CORPUS, load_evaluation_suite(SUITE_PATH))
    json_out = tmp_path / "evaluation-report.json"
    markdown_out = tmp_path / "evaluation-report.md"

    write_json_report(report, json_out)
    write_markdown_report(report, markdown_out)

    payload = json.loads(json_out.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["trust_layer_status"] == "pass"
    assert payload["retrieval_config"]["top_k"] == "per_case"
    assert payload["metrics"]["stale_document_exclusion_rate"] == "24/24"
    assert "Biotech RAG Assistant trust-layer report" in markdown_out.read_text(
        encoding="utf-8"
    )
