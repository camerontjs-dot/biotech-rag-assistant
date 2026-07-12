"""Command-line interface for the controlled-document retrieval pilot."""

from __future__ import annotations

import json
from pathlib import Path

import click

from biotech_rag_assistant import __version__
from biotech_rag_assistant.answer import AnswerAssemblyError, build_extractive_answer
from biotech_rag_assistant.citations import (
    CitationFixtureError,
    load_answer_fixture,
    load_retrieved_results,
    validate_answer_citations,
)
from biotech_rag_assistant.corpus import CorpusValidationError, load_corpus, validate_corpus
from biotech_rag_assistant.evaluation import (
    EvaluationFixtureError,
    load_evaluation_suite,
    run_evaluation_suite,
    write_json_report,
    write_markdown_report,
)
from biotech_rag_assistant.onboarding import (
    OnboardingError,
    onboard_corpus,
)
from biotech_rag_assistant.onboarding import (
    write_json_report as write_onboarding_json_report,
)
from biotech_rag_assistant.onboarding import (
    write_markdown_report as write_onboarding_markdown_report,
)
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval


@click.group()
@click.version_option(version=__version__, prog_name="biotech-rag")
def cli() -> None:
    """Validate and retrieve from synthetic controlled-document corpora."""


@cli.command("validate-corpus")
@click.argument(
    "corpus_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
def validate_corpus_command(corpus_dir: Path) -> None:
    """Validate corpus sidecars, source hashes, and retrievable document status."""
    _documents, report = validate_corpus(corpus_dir)
    click.echo(f"Metadata files seen: {report.metadata_files_seen}")
    click.echo(f"Documents valid: {report.documents_valid}")
    click.echo(f"Documents retrievable: {report.documents_retrievable}")
    click.echo(f"Documents excluded by status: {report.documents_excluded}")
    if report.valid:
        click.echo("Corpus validation passed")
        return

    click.echo("Corpus validation failed", err=True)
    for issue in report.issues:
        click.echo(f"- {issue.path}: {issue.message}", err=True)
    raise click.ClickException("corpus validation failed")


@cli.command("onboard-corpus")
@click.argument(
    "messy_corpus_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option(
    "--mapping",
    "mapping_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Override the default metadata-map.yaml.",
)
@click.option(
    "--register",
    "register_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    help="Override the default incoming/source-register.yaml.",
)
@click.option(
    "--output",
    "output_dir",
    required=True,
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help="Normalized corpus output directory.",
)
@click.option(
    "--report-out",
    "report_out",
    required=True,
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="JSON onboarding coverage report path.",
)
@click.option(
    "--markdown-out",
    "markdown_out",
    type=click.Path(file_okay=True, dir_okay=False, path_type=Path),
    help="Optional Markdown onboarding coverage report path.",
)
@click.option("--dry-run", is_flag=True, help="Write reports without writing output corpus.")
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite the output directory when it already exists and is not empty.",
)
@click.option(
    "--require-no-review",
    is_flag=True,
    help="Fail if any source needs review or is rejected.",
)
@click.option("--json", "json_output", is_flag=True, help="Emit report JSON to stdout.")
def onboard_corpus_command(
    messy_corpus_dir: Path,
    mapping_path: Path | None,
    register_path: Path | None,
    output_dir: Path,
    report_out: Path,
    markdown_out: Path | None,
    dry_run: bool,
    force: bool,
    require_no_review: bool,
    json_output: bool,
) -> None:
    """Map messy client-like sources into the clean corpus contract."""
    try:
        report = onboard_corpus(
            messy_corpus_dir,
            output_dir=output_dir,
            mapping_path=mapping_path,
            register_path=register_path,
            dry_run=dry_run,
            force=force,
        )
    except OnboardingError as exc:
        raise click.ClickException(str(exc)) from exc

    write_onboarding_json_report(report, report_out)
    if markdown_out is not None:
        write_onboarding_markdown_report(report, markdown_out)

    if json_output:
        click.echo(json.dumps(report.to_cli_record(), indent=2, sort_keys=True))
    else:
        click.echo(f"Input documents: {report.input_document_count}")
        click.echo(f"Emitted documents: {report.emitted_document_count}")
        for state, count in report.state_counts.items():
            click.echo(f"{state}: {count}")

    if require_no_review and (
        report.state_counts["needs_review"] or report.state_counts["rejected"]
    ):
        raise click.ClickException("onboarding produced review or rejection records")


@cli.command("retrieve")
@click.argument(
    "corpus_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--query", "query_text", required=True, help="Question or search text.")
@click.option("--top-k", default=5, show_default=True, type=click.IntRange(min=1))
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def retrieve_command(
    corpus_dir: Path,
    query_text: str,
    top_k: int,
    json_output: bool,
) -> None:
    """Retrieve approved/effective chunks from a validated corpus."""
    try:
        corpus = load_corpus(corpus_dir)
    except CorpusValidationError as exc:
        for issue in exc.report.issues:
            click.echo(f"- {issue.path}: {issue.message}", err=True)
        raise click.ClickException("corpus validation failed") from exc

    hits = run_retrieval(
        corpus.documents,
        query_text,
        RetrievalConfig(top_k=top_k),
    )
    records = [hit.to_cli_record() for hit in hits]

    if json_output:
        payload = {
            "query": query_text,
            "retrievable_documents": corpus.report.documents_retrievable,
            "hits": records,
        }
        click.echo(json.dumps(payload, indent=2))
        return

    if not records:
        click.echo("No retrievable chunks matched the query.")
        return

    for record in records:
        click.echo(
            f"{record['rank']}. {record['doc_id']} {record['chunk_id']} "
            f"score={record['score']:.4f}"
        )
        click.echo(f"   {record['section_heading']} ({record['line_or_page_span']})")
        click.echo(f"   {record['source_file_path']}")


@cli.command("answer")
@click.argument(
    "corpus_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.option("--query", "query_text", required=True, help="Question or search text.")
@click.option("--top-k", default=3, show_default=True, type=click.IntRange(min=1))
def answer_command(corpus_dir: Path, query_text: str, top_k: int) -> None:
    """Return a deterministic extractive answer with validated citations."""
    try:
        corpus = load_corpus(corpus_dir)
    except CorpusValidationError as exc:
        for issue in exc.report.issues:
            click.echo(f"- {issue.path}: {issue.message}", err=True)
        raise click.ClickException("corpus validation failed") from exc

    hits = run_retrieval(
        corpus.documents,
        query_text,
        RetrievalConfig(top_k=top_k),
    )
    try:
        answer = build_extractive_answer(query_text, hits)
    except AnswerAssemblyError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(answer.to_cli_record(), indent=2))


@cli.command("validate-citations")
@click.argument(
    "retrieved_results_json",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.argument(
    "answer_fixture_json",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def validate_citations_command(
    retrieved_results_json: Path,
    answer_fixture_json: Path,
    json_output: bool,
) -> None:
    """Validate that answer citations resolve to retrieved chunks."""
    try:
        retrieved_results = load_retrieved_results(retrieved_results_json)
        answer_fixture = load_answer_fixture(answer_fixture_json)
    except CitationFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    result = validate_answer_citations(retrieved_results, answer_fixture)
    if json_output:
        click.echo(json.dumps(result.to_cli_record(), indent=2))
    else:
        click.echo(f"Metric: {result.metric_name}")
        click.echo(
            "citation_resolves_to_retrieved_chunk: "
            f"{result.citation_resolves_to_retrieved_chunk}"
        )
        click.echo(f"Resolved citations: {result.resolved_citation_count}")
        if result.issues:
            click.echo("Issues:")
            for issue in result.issues:
                chunk_suffix = f" ({issue.chunk_id})" if issue.chunk_id else ""
                click.echo(f"- {issue.code}{chunk_suffix}: {issue.message}")

    if not result.valid:
        raise click.ClickException("citation validation failed")


@cli.command("evaluate")
@click.argument(
    "corpus_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "evaluation_suite_json",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
)
@click.option("--json-out", type=click.Path(file_okay=True, dir_okay=False, path_type=Path))
@click.option("--markdown-out", type=click.Path(file_okay=True, dir_okay=False, path_type=Path))
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
def evaluate_command(
    corpus_dir: Path,
    evaluation_suite_json: Path,
    json_out: Path | None,
    markdown_out: Path | None,
    json_output: bool,
) -> None:
    """Run a golden-question evaluation suite over a corpus."""
    try:
        suite = load_evaluation_suite(evaluation_suite_json)
        report = run_evaluation_suite(corpus_dir, suite)
    except CorpusValidationError as exc:
        for issue in exc.report.issues:
            click.echo(f"- {issue.path}: {issue.message}", err=True)
        raise click.ClickException("corpus validation failed") from exc
    except EvaluationFixtureError as exc:
        raise click.ClickException(str(exc)) from exc

    if json_out is not None:
        write_json_report(report, json_out)
    if markdown_out is not None:
        write_markdown_report(report, markdown_out)

    if json_output:
        click.echo(json.dumps(report.to_cli_record(), indent=2))
    else:
        click.echo(f"Suite: {report.suite_name}")
        click.echo(f"Trust layer status: {report.trust_layer_status}")
        click.echo(f"Cases passed: {report.passed_case_count}/{report.case_count}")
        for name, value in report.metrics.items():
            click.echo(f"{name}: {value}")

    if not report.valid:
        raise click.ClickException("evaluation failed")


@cli.command("serve")
@click.option("--host", "host", default=None, help="Bind host (overrides BIOTECH_RAG_HOST).")
@click.option(
    "--port", "port", default=None, type=int, help="Bind port (overrides BIOTECH_RAG_PORT)."
)
def serve_command(host: str | None, port: int | None) -> None:
    """Run the FastAPI transport layer over uvicorn, reading config from the environment."""
    import uvicorn

    from biotech_rag_assistant.api import create_app
    from biotech_rag_assistant.api.config import ApiConfig

    config = ApiConfig.from_env()
    app = create_app(config)
    uvicorn.run(app, host=host or config.host, port=port or config.port)


@cli.command("demo")
@click.option("--host", "host", default=None, help="Bind host (overrides BIOTECH_RAG_HOST).")
@click.option(
    "--port", "port", default=None, type=int, help="Bind port (overrides BIOTECH_RAG_PORT)."
)
def demo_command(host: str | None, port: int | None) -> None:
    """Run the transport layer plus the demo chat UI (served at the root path)."""
    import uvicorn

    from biotech_rag_assistant.api.config import ApiConfig
    from biotech_rag_assistant.api.webui import create_demo_app

    config = ApiConfig.from_env()
    app = create_demo_app(config)
    click.echo(f"Demo UI: http://{host or config.host}:{port or config.port}/")
    uvicorn.run(app, host=host or config.host, port=port or config.port)
