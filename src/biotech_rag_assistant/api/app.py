"""FastAPI pure-transport layer for the controlled-document retrieval pilot.

The HTTP routes call the same core functions as the CLI (``run_retrieval``,
``build_extractive_answer``, ``validate_answer_citations``, ``run_evaluation_suite``) and
serialize the same ``to_cli_record()`` output, so API JSON matches the CLI. No core logic
lives here. Corpora are loaded and validated once at startup from the configured allowlist;
requests select a bundle by name, never by path.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse

from biotech_rag_assistant import __version__
from biotech_rag_assistant.answer import AnswerAssemblyError, build_extractive_answer
from biotech_rag_assistant.api.audit import emit_audit_record
from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.api.review_routing import assess_review
from biotech_rag_assistant.api.schemas import (
    AnswerRequest,
    CorpusRequest,
    EvaluateRequest,
    RetrieveRequest,
    ValidateCitationsRequest,
)
from biotech_rag_assistant.api.security import require_api_key
from biotech_rag_assistant.citations import validate_answer_citations
from biotech_rag_assistant.corpus import CorpusValidationError, load_corpus, validate_corpus
from biotech_rag_assistant.evaluation import run_evaluation_suite
from biotech_rag_assistant.models import Corpus
from biotech_rag_assistant.retrieval import RetrievalConfig, build_retriever, query_retriever

HEALTH_PATH = "/health"


def create_app(config: ApiConfig | None = None) -> FastAPI:
    """Build the transport app, loading and validating every allowlisted corpus at startup."""
    config = config or ApiConfig.from_env()
    corpora: dict[str, Corpus] = {
        name: load_corpus(path) for name, path in config.corpora.items()
    }
    # Chunk + index each corpus once at startup; requests reuse the prebuilt retriever rather
    # than re-chunking and rebuilding BM25 per call.
    retrievers = {name: build_retriever(corpus.documents) for name, corpus in corpora.items()}

    app = FastAPI(title="Biotech RAG Assistant transport", version=__version__)
    app.state.config = config
    app.state.corpora = corpora
    app.state.retrievers = retrievers

    @app.middleware("http")
    async def audit_and_request_id(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.audit_summary = {}
        # Default to 500 so an unhandled exception below still records a faithful audit line.
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            # finally so every non-health request emits exactly one audit record even when the
            # handler raises (ADR-010 invariant); on an unhandled 500 the response and its
            # X-Request-ID header may be absent, but the audit record is not.
            if request.url.path != HEALTH_PATH:
                record = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "request_id": request_id,
                    "route": request.url.path,
                    "method": request.method,
                    "status_code": status_code,
                    **getattr(request.state, "audit_summary", {}),
                }
                emit_audit_record(record, request.app.state.config.audit_log_path)

    @app.exception_handler(CorpusValidationError)
    async def handle_corpus_validation_error(
        request: Request,
        exc: CorpusValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "corpus validation failed",
                "issues": [issue.model_dump() for issue in exc.report.issues],
            },
        )

    @app.get(HEALTH_PATH)
    async def health(request: Request) -> dict[str, Any]:
        cfg: ApiConfig = request.app.state.config
        return {
            "status": "ok",
            "version": __version__,
            "corpora": sorted(cfg.corpora),
            "default_corpus": cfg.default_corpus,
        }

    @app.post("/validate-corpus", dependencies=[Depends(require_api_key)])
    async def validate_corpus_route(
        request: Request,
        body: CorpusRequest | None = None,
    ) -> dict[str, Any]:
        cfg: ApiConfig = request.app.state.config
        name = _resolve_corpus_name(cfg, body.corpus if body else None)
        _documents, report = validate_corpus(cfg.corpora[name])
        request.state.audit_summary = {"corpus": name, "valid": report.valid}
        return {
            "corpus": name,
            "metadata_files_seen": report.metadata_files_seen,
            "documents_valid": report.documents_valid,
            "documents_retrievable": report.documents_retrievable,
            "documents_excluded": report.documents_excluded,
            "issues": [issue.model_dump() for issue in report.issues],
            "valid": report.valid,
        }

    @app.post("/retrieve", dependencies=[Depends(require_api_key)])
    async def retrieve_route(request: Request, body: RetrieveRequest) -> dict[str, Any]:
        cfg: ApiConfig = request.app.state.config
        name = _resolve_corpus_name(cfg, body.corpus)
        corpus: Corpus = request.app.state.corpora[name]
        retriever = request.app.state.retrievers[name]
        hits = query_retriever(retriever, body.query, RetrievalConfig(top_k=body.top_k))
        records = [hit.to_cli_record() for hit in hits]
        request.state.audit_summary = {
            "corpus": name,
            "query": body.query,
            "top_k": body.top_k,
            "hit_chunk_ids": [record["chunk_id"] for record in records],
        }
        return {
            "query": body.query,
            "retrievable_documents": corpus.report.documents_retrievable,
            "hits": records,
        }

    @app.post("/answer", dependencies=[Depends(require_api_key)])
    async def answer_route(request: Request, body: AnswerRequest) -> dict[str, Any]:
        cfg: ApiConfig = request.app.state.config
        name = _resolve_corpus_name(cfg, body.corpus)
        retriever = request.app.state.retrievers[name]
        retrieval_config = RetrievalConfig(top_k=body.top_k)
        hits = query_retriever(retriever, body.query, retrieval_config)
        try:
            answer = build_extractive_answer(body.query, hits)
        except AnswerAssemblyError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        review = assess_review(
            answer,
            hits,
            score_floor=retrieval_config.score_floor,
            low_score_margin=cfg.low_score_margin,
        )
        request.state.audit_summary = {
            "corpus": name,
            "query": body.query,
            "top_k": body.top_k,
            "outcome": answer.outcome,
            "citation_valid": answer.citation_validation.valid,
            "review_recommended": review.review_recommended,
            "review_reasons": review.reasons,
        }
        return {**answer.to_cli_record(), "review_recommendation": review.model_dump()}

    @app.post("/validate-citations", dependencies=[Depends(require_api_key)])
    async def validate_citations_route(
        request: Request,
        body: ValidateCitationsRequest,
    ) -> dict[str, Any]:
        result = validate_answer_citations(body.retrieved_results, body.answer_fixture)
        request.state.audit_summary = {
            "expected_outcome": body.answer_fixture.expected_outcome,
            "citation_valid": result.valid,
        }
        return result.to_cli_record()

    @app.post("/evaluate", dependencies=[Depends(require_api_key)])
    async def evaluate_route(request: Request, body: EvaluateRequest) -> dict[str, Any]:
        cfg: ApiConfig = request.app.state.config
        name = _resolve_corpus_name(cfg, body.corpus)
        report = run_evaluation_suite(cfg.corpora[name], body.suite)
        request.state.audit_summary = {
            "corpus": name,
            "suite_name": body.suite.suite_name,
            "trust_layer_status": report.trust_layer_status,
            "passed_case_count": report.passed_case_count,
            "case_count": report.case_count,
        }
        return report.to_cli_record()

    return app


def _resolve_corpus_name(config: ApiConfig, requested: str | None) -> str:
    """Map an optional request corpus name onto the allowlist (404 if unknown)."""
    name = requested or config.default_corpus
    if name not in config.corpora:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown corpus: {name}",
        )
    return name


app = create_app()
