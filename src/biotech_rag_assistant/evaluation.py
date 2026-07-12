"""Starter evaluation harness for the controlled-document retrieval pilot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from biotech_rag_assistant.answer import AnswerAssemblyError, build_extractive_answer
from biotech_rag_assistant.citations import (
    AnswerFixture,
    CitationOutcome,
    RetrievedChunkRecord,
    RetrievedResultsPayload,
    validate_answer_citations,
)
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import (
    BM25Retriever,
    RetrievalConfig,
    build_retriever,
    query_retriever,
)

LiteralPassFail = Literal["pass", "fail"]


class EvaluationFixtureError(Exception):
    """Raised when an evaluation fixture cannot be loaded."""


class EvaluationCase(BaseModel):
    """One golden question with retrieval and optional citation expectations."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    expected_outcome: CitationOutcome
    top_k: int = Field(default=3, ge=1)
    expected_source_doc_ids: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    forbidden_doc_ids: list[str] = Field(default_factory=list)
    expect_no_hits: bool = False
    answer_fixture: AnswerFixture | None = None
    expected_citation_resolves_to_retrieved_chunk: bool | None = None
    expected_citation_issue_codes: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_citation_expectations(self) -> EvaluationCase:
        if self.answer_fixture is None:
            if self.expected_citation_resolves_to_retrieved_chunk is not None:
                raise ValueError(
                    "expected_citation_resolves_to_retrieved_chunk requires answer_fixture"
                )
            if self.expected_citation_issue_codes:
                raise ValueError("expected_citation_issue_codes requires answer_fixture")
            return self

        if self.answer_fixture.expected_outcome != self.expected_outcome:
            raise ValueError("answer_fixture.expected_outcome must match expected_outcome")
        if self.expected_citation_resolves_to_retrieved_chunk is None:
            raise ValueError(
                "answer_fixture cases must set "
                "expected_citation_resolves_to_retrieved_chunk"
            )
        return self


class EvaluationSuite(BaseModel):
    """A small suite of golden questions for the synthetic corpus."""

    model_config = ConfigDict(extra="forbid")

    suite_name: str = Field(min_length=1)
    cases: list[EvaluationCase] = Field(min_length=1)


class CaseEvaluationResult(BaseModel):
    """Observed result for one golden question."""

    model_config = ConfigDict(extra="forbid")

    case_id: str
    passed: bool
    expected_outcome: CitationOutcome
    hit_chunk_ids: list[str]
    hit_doc_ids: list[str]
    retrieval_expectation_passed: bool
    stale_document_exclusion_passed: bool
    refusal_expectation_passed: bool
    citation_expectation_passed: bool | None = None
    citation_resolves_to_retrieved_chunk: bool | None = None
    citation_issue_codes: list[str] = Field(default_factory=list)
    generated_answer_outcome: CitationOutcome | None = None
    generated_answer_outcome_passed: bool
    generated_answer_citation_validation_passed: bool
    issues: list[str] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """Evaluation report that can be written as JSON or Markdown."""

    model_config = ConfigDict(extra="forbid")

    suite_name: str
    trust_layer_status: LiteralPassFail
    corpus_summary: dict[str, object]
    retrieval_config: dict[str, object]
    case_count: int = Field(ge=0)
    passed_case_count: int = Field(ge=0)
    metrics: dict[str, str]
    cases: list[CaseEvaluationResult]

    @property
    def valid(self) -> bool:
        return self.case_count == self.passed_case_count

    def to_cli_record(self) -> dict[str, object]:
        return {
            "valid": self.valid,
            "trust_layer_status": self.trust_layer_status,
            "suite_name": self.suite_name,
            "corpus_summary": self.corpus_summary,
            "retrieval_config": self.retrieval_config,
            "case_count": self.case_count,
            "passed_case_count": self.passed_case_count,
            "metrics": self.metrics,
            "cases": [case.model_dump() for case in self.cases],
        }


def load_evaluation_suite(path: Path) -> EvaluationSuite:
    """Load a golden-question suite from JSON."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvaluationFixtureError(f"could not read {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise EvaluationFixtureError(f"invalid JSON in {path}: {exc}") from exc

    try:
        return EvaluationSuite.model_validate(raw)
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            field = ".".join(str(part) for part in error["loc"])
            messages.append(f"{field}: {error['msg']}")
        message = f"invalid evaluation suite {path}: {'; '.join(messages)}"
        raise EvaluationFixtureError(message) from exc


def run_evaluation_suite(corpus_dir: Path, suite: EvaluationSuite) -> EvaluationReport:
    """Run golden questions against the current deterministic retrieval baseline."""
    corpus = load_corpus(corpus_dir)
    retrieval_config = RetrievalConfig()
    retriever = build_retriever(corpus.documents)
    case_results = [
        _run_case(retriever, case, retrieval_config) for case in suite.cases
    ]
    passed_count = sum(1 for result in case_results if result.passed)
    trust_layer_status: LiteralPassFail = (
        "pass" if passed_count == len(case_results) else "fail"
    )
    return EvaluationReport(
        suite_name=suite.suite_name,
        trust_layer_status=trust_layer_status,
        corpus_summary={
            "corpus_dir": str(corpus.corpus_dir),
            "metadata_files_seen": corpus.report.metadata_files_seen,
            "documents_valid": corpus.report.documents_valid,
            "documents_retrievable": corpus.report.documents_retrievable,
            "documents_excluded": corpus.report.documents_excluded,
        },
        retrieval_config={
            **retrieval_config.to_cli_record(),
            "top_k": "per_case",
        },
        case_count=len(case_results),
        passed_case_count=passed_count,
        metrics=_summarize_metrics(case_results),
        cases=case_results,
    )


def render_markdown_report(report: EvaluationReport) -> str:
    """Render an evaluation report for portfolio inspection."""
    lines = [
        "# Biotech RAG Assistant trust-layer report",
        "",
        "This report measures retrieval behavior and structural citation resolution "
        "over synthetic fixtures. `citation_resolves_to_retrieved_chunk` means a cited "
        "`chunk_id` appeared in retrieved results. It does not measure semantic support.",
        "",
        "## Summary",
        "",
        f"- Suite: `{report.suite_name}`",
        f"- Trust layer status: {report.trust_layer_status}",
        f"- Cases passed: {report.passed_case_count}/{report.case_count}",
        f"- Overall status: {'pass' if report.valid else 'fail'}",
        "",
        "## Corpus/config",
        "",
        f"- Corpus directory: `{report.corpus_summary['corpus_dir']}`",
        f"- Metadata files seen: {report.corpus_summary['metadata_files_seen']}",
        f"- Documents valid: {report.corpus_summary['documents_valid']}",
        f"- Documents retrievable: {report.corpus_summary['documents_retrievable']}",
        f"- Documents excluded by status: {report.corpus_summary['documents_excluded']}",
        f"- Retrieval method: `{report.retrieval_config['method']}`",
        f"- Top k: {report.retrieval_config['top_k']}",
        f"- Score floor: {report.retrieval_config['score_floor']}",
        "",
        "## Metrics",
        "",
    ]
    for name, value in report.metrics.items():
        lines.append(f"- `{name}`: {value}")

    lines.extend(
        [
            "",
            "## Case table",
            "",
            "| Case | Passed | Outcome | Hits | Fixture citation issues | "
            "Generated citation check | Issues |",
            "|---|---:|---|---|---|---:|---|",
        ]
    )
    for case in report.cases:
        issues = "; ".join(case.issues) if case.issues else "none"
        fixture_issues = (
            ", ".join(case.citation_issue_codes)
            if case.citation_issue_codes
            else ("none" if case.citation_expectation_passed is not None else "n/a")
        )
        lines.append(
            f"| `{case.case_id}` | {str(case.passed).lower()} | "
            f"{case.generated_answer_outcome or 'n/a'} | "
            f"{', '.join(case.hit_chunk_ids) or 'none'} | "
            f"{fixture_issues} | "
            f"{str(case.generated_answer_citation_validation_passed).lower()} | {issues} |"
        )
    lines.extend(
        [
            "",
            "## Limits",
            "",
            "This report exercises a synthetic corpus and deterministic BM25 retrieval. "
            "The generated answer is extractive: it copies retrieved spans and tags them "
            "with citations. It does not verify regulatory compliance, measure semantic "
            "support, or test an LLM.",
            "",
        ]
    )
    return "\n".join(lines)


def write_json_report(report: EvaluationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report.to_cli_record(), indent=2) + "\n", encoding="utf-8")


def write_markdown_report(report: EvaluationReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(report), encoding="utf-8")


def _run_case(
    retriever: BM25Retriever,
    case: EvaluationCase,
    base_config: RetrievalConfig,
) -> CaseEvaluationResult:
    config = base_config.model_copy(update={"top_k": case.top_k})
    hits = query_retriever(retriever, case.question, config)
    records = [hit.to_cli_record() for hit in hits]
    hit_chunk_ids = [str(record["chunk_id"]) for record in records]
    hit_doc_ids = [str(record["doc_id"]) for record in records]
    hit_statuses = [str(record["status"]) for record in records]
    issues: list[str] = []

    retrieval_passed = True
    for doc_id in case.expected_source_doc_ids:
        if doc_id not in hit_doc_ids:
            retrieval_passed = False
            issues.append(f"expected_source_doc_missing:{doc_id}")
    for chunk_id in case.expected_chunk_ids:
        if chunk_id not in hit_chunk_ids:
            retrieval_passed = False
            issues.append(f"expected_chunk_missing:{chunk_id}")

    stale_passed = True
    for doc_id in case.forbidden_doc_ids:
        if doc_id in hit_doc_ids:
            stale_passed = False
            issues.append(f"forbidden_doc_retrieved:{doc_id}")
    for status in hit_statuses:
        if status not in {"Approved", "Effective"}:
            stale_passed = False
            issues.append(f"stale_status_retrieved:{status}")

    refusal_passed = True
    if case.expect_no_hits and hits:
        refusal_passed = False
        issues.append("expected_no_hits")
    if case.expected_outcome == "answer" and not hits:
        retrieval_passed = False
        issues.append("answer_expected_but_no_hits")

    citation_passed: bool | None = None
    citation_resolves: bool | None = None
    citation_issue_codes: list[str] = []
    if case.answer_fixture is not None:
        retrieved_payload = RetrievedResultsPayload(
            query=case.question,
            hits=[RetrievedChunkRecord.model_validate(record) for record in records],
        )
        citation_result = validate_answer_citations(retrieved_payload, case.answer_fixture)
        citation_resolves = citation_result.citation_resolves_to_retrieved_chunk
        citation_issue_codes = sorted(issue.code for issue in citation_result.issues)
        expected_codes = sorted(case.expected_citation_issue_codes)
        citation_passed = (
            citation_resolves == case.expected_citation_resolves_to_retrieved_chunk
            and citation_issue_codes == expected_codes
        )
        if not citation_passed:
            issues.append(
                "citation_expectation_mismatch:"
                f"expected_resolves={case.expected_citation_resolves_to_retrieved_chunk},"
                f"observed_resolves={citation_resolves},"
                f"expected_codes={expected_codes},"
                f"observed_codes={citation_issue_codes}"
            )

    generated_answer_outcome: CitationOutcome | None = None
    generated_answer_outcome_passed = False
    generated_answer_citation_validation_passed = False
    try:
        generated_answer = build_extractive_answer(case.question, hits)
        generated_answer_outcome = generated_answer.outcome
        generated_answer_outcome_passed = generated_answer.outcome == case.expected_outcome
        generated_answer_citation_validation_passed = generated_answer.citation_validation.valid
        if not generated_answer_outcome_passed:
            issues.append(
                "generated_answer_outcome_mismatch:"
                f"expected={case.expected_outcome},observed={generated_answer.outcome}"
            )
    except AnswerAssemblyError as exc:
        issues.append(f"generated_answer_citation_validation_failed:{exc}")

    pass_flags = [
        retrieval_passed,
        stale_passed,
        refusal_passed,
        generated_answer_outcome_passed,
        generated_answer_citation_validation_passed,
    ]
    if citation_passed is not None:
        pass_flags.append(citation_passed)

    return CaseEvaluationResult(
        case_id=case.case_id,
        passed=all(pass_flags),
        expected_outcome=case.expected_outcome,
        hit_chunk_ids=hit_chunk_ids,
        hit_doc_ids=hit_doc_ids,
        retrieval_expectation_passed=retrieval_passed,
        stale_document_exclusion_passed=stale_passed,
        refusal_expectation_passed=refusal_passed,
        citation_expectation_passed=citation_passed,
        citation_resolves_to_retrieved_chunk=citation_resolves,
        citation_issue_codes=citation_issue_codes,
        generated_answer_outcome=generated_answer_outcome,
        generated_answer_outcome_passed=generated_answer_outcome_passed,
        generated_answer_citation_validation_passed=generated_answer_citation_validation_passed,
        issues=issues,
    )


def _summarize_metrics(case_results: list[CaseEvaluationResult]) -> dict[str, str]:
    citation_cases = [
        result
        for result in case_results
        if result.citation_resolves_to_retrieved_chunk is not None
    ]
    no_hit_cases = [
        result for result in case_results if result.expected_outcome == "refusal"
    ]
    return {
        "case_pass_rate": _fraction(
            sum(1 for result in case_results if result.passed),
            len(case_results),
        ),
        "retrieval_expectation_match_rate": _fraction(
            sum(1 for result in case_results if result.retrieval_expectation_passed),
            len(case_results),
        ),
        "stale_document_exclusion_rate": _fraction(
            sum(1 for result in case_results if result.stale_document_exclusion_passed),
            len(case_results),
        ),
        "refusal_expectation_match_rate": _fraction(
            sum(1 for result in no_hit_cases if result.refusal_expectation_passed),
            len(no_hit_cases),
        ),
        "citation_resolves_to_retrieved_chunk_rate": _fraction(
            sum(
                1
                for result in citation_cases
                if result.citation_resolves_to_retrieved_chunk
            ),
            len(citation_cases),
        ),
        "citation_expectation_match_rate": _fraction(
            sum(1 for result in citation_cases if result.citation_expectation_passed),
            len(citation_cases),
        ),
        "generated_answer_outcome_match_rate": _fraction(
            sum(1 for result in case_results if result.generated_answer_outcome_passed),
            len(case_results),
        ),
        "generated_answer_citation_validation_rate": _fraction(
            sum(
                1
                for result in case_results
                if result.generated_answer_citation_validation_passed
            ),
            len(case_results),
        ),
    }


def _fraction(numerator: int, denominator: int) -> str:
    if denominator == 0:
        return "n/a"
    return f"{numerator}/{denominator}"
