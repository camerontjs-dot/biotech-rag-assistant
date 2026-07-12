"""Transport-layer tests for the controlled-document retrieval pilot.

These prove the HTTP layer is *pure transport*: for the same input, API JSON equals the
CLI ``--json`` output (parity). They also cover the trust boundary (non-retrievable docs
never surface), the security posture (API key, corpus allowlist, no path inputs), the
advisory review-routing signal, and audit traceability.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from fastapi.testclient import TestClient

from biotech_rag_assistant.api import create_app
from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.cli import cli
from biotech_rag_assistant.models import RETRIEVABLE_STATUSES

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
GOLDEN_QUESTIONS = DEMO_CORPUS / "evaluation/golden-questions.json"
CITATION_FIXTURES = ROOT / "tests/fixtures/citation-validation"

GREEN_QUERY = "viable excursion affected product lots immediate containment"
NO_HIT_QUERY = "zzzz qqqq impossible-token"


def make_config(**overrides: object) -> ApiConfig:
    """Build a config bound to the bundled synthetic corpus, with optional overrides."""
    params: dict[str, object] = {
        "corpora": {"synthetic": DEMO_CORPUS},
        "default_corpus": "synthetic",
    }
    params.update(overrides)
    return ApiConfig(**params)  # type: ignore[arg-type]


def make_client(**overrides: object) -> TestClient:
    return TestClient(create_app(make_config(**overrides)))


def cli_json(args: list[str]) -> dict:
    """Run a CLI command that emits JSON on success and return the parsed object."""
    result = CliRunner().invoke(cli, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


# --- Parity: the proof of "pure transport" (compare parsed objects, not whitespace) ---


def test_retrieve_matches_cli_json() -> None:
    client = make_client()
    api = client.post("/retrieve", json={"query": GREEN_QUERY, "top_k": 1}).json()
    cli_out = cli_json(
        ["retrieve", str(DEMO_CORPUS), "--query", GREEN_QUERY, "--top-k", "1", "--json"]
    )
    assert api == cli_out


def test_answer_minus_review_matches_cli_json() -> None:
    client = make_client()
    api = client.post("/answer", json={"query": GREEN_QUERY, "top_k": 1}).json()
    assert "review_recommendation" in api
    api_core = {key: value for key, value in api.items() if key != "review_recommendation"}
    cli_out = cli_json(["answer", str(DEMO_CORPUS), "--query", GREEN_QUERY, "--top-k", "1"])
    assert api_core == cli_out


def test_validate_citations_matches_cli_json() -> None:
    client = make_client()
    retrieved = json.loads((CITATION_FIXTURES / "retrieval-valid.json").read_text("utf-8"))
    fixture = json.loads((CITATION_FIXTURES / "answer-valid.json").read_text("utf-8"))
    api = client.post(
        "/validate-citations",
        json={"retrieved_results": retrieved, "answer_fixture": fixture},
    ).json()
    cli_out = cli_json(
        [
            "validate-citations",
            str(CITATION_FIXTURES / "retrieval-valid.json"),
            str(CITATION_FIXTURES / "answer-valid.json"),
            "--json",
        ]
    )
    assert api == cli_out
    assert api["valid"] is True


def test_evaluate_matches_cli_json() -> None:
    client = make_client()
    suite = json.loads(GOLDEN_QUESTIONS.read_text("utf-8"))
    api = client.post("/evaluate", json={"suite": suite}).json()
    cli_out = cli_json(["evaluate", str(DEMO_CORPUS), str(GOLDEN_QUESTIONS), "--json"])
    assert api == cli_out
    assert api["trust_layer_status"] == "pass"


# --- Trust boundary: non-retrievable documents never surface through transport ---


def test_validate_corpus_reports_excluded_documents() -> None:
    client = make_client()
    payload = client.post("/validate-corpus", json={}).json()
    assert payload["valid"] is True
    assert payload["documents_retrievable"] == 8
    assert payload["documents_excluded"] == 2


def test_retrieve_returns_only_retrievable_statuses() -> None:
    client = make_client()
    query = "document control current approved version draft obsolete rule"
    payload = client.post(
        "/retrieve",
        json={"query": query, "top_k": 50},
    ).json()
    assert payload["hits"]
    for hit in payload["hits"]:
        assert hit["status"] in RETRIEVABLE_STATUSES


def test_validate_citations_reports_failure_with_200() -> None:
    client = make_client()
    retrieved = json.loads((CITATION_FIXTURES / "retrieval-valid.json").read_text("utf-8"))
    fixture = json.loads(
        (CITATION_FIXTURES / "answer-hallucinated-citation.json").read_text("utf-8")
    )
    response = client.post(
        "/validate-citations",
        json={"retrieved_results": retrieved, "answer_fixture": fixture},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["valid"] is False
    assert any(issue["code"] == "unresolved_citation" for issue in payload["issues"])


# --- Security posture: API key, corpus allowlist, no filesystem path inputs ---


def test_api_key_enforced_on_routes_but_not_health() -> None:
    client = make_client(api_key="secret-key")
    assert client.get("/health").status_code == 200
    assert client.post("/retrieve", json={"query": GREEN_QUERY}).status_code == 401
    wrong = client.post("/retrieve", json={"query": GREEN_QUERY}, headers={"X-API-Key": "nope"})
    assert wrong.status_code == 401
    ok = client.post(
        "/retrieve", json={"query": GREEN_QUERY}, headers={"X-API-Key": "secret-key"}
    )
    assert ok.status_code == 200


def test_unknown_corpus_name_returns_404() -> None:
    client = make_client()
    response = client.post("/retrieve", json={"query": GREEN_QUERY, "corpus": "does-not-exist"})
    assert response.status_code == 404


def test_filesystem_path_input_is_rejected() -> None:
    client = make_client()
    response = client.post("/retrieve", json={"query": GREEN_QUERY, "corpus_dir": "/etc/passwd"})
    assert response.status_code == 422


# --- Advisory review-routing (mechanical; does not change the answer outcome contract) ---


def test_refusal_recommends_review() -> None:
    client = make_client()
    payload = client.post("/answer", json={"query": NO_HIT_QUERY}).json()
    assert payload["outcome"] == "refusal"
    review = payload["review_recommendation"]
    assert review["review_recommended"] is True
    assert "refusal_no_supporting_documents" in review["reasons"]


def test_green_answer_not_flagged_by_default() -> None:
    client = make_client()
    payload = client.post("/answer", json={"query": GREEN_QUERY, "top_k": 1}).json()
    assert payload["outcome"] == "answer"
    review = payload["review_recommendation"]
    assert review["review_recommended"] is False
    assert review["reasons"] == []


def test_low_top_score_flagged_when_margin_exceeds_score() -> None:
    client = make_client(low_score_margin=100.0)
    payload = client.post("/answer", json={"query": GREEN_QUERY, "top_k": 1}).json()
    assert payload["outcome"] == "answer"
    review = payload["review_recommendation"]
    assert review["review_recommended"] is True
    assert "low_top_score" in review["reasons"]


# --- Traceability: request id header + per-request audit record ---


def test_request_id_header_present() -> None:
    client = make_client()
    response = client.get("/health")
    assert response.headers.get("X-Request-ID")


def test_audit_record_appended_as_jsonl(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    client = make_client(audit_log_path=audit_path)
    response = client.post("/retrieve", json={"query": GREEN_QUERY, "top_k": 1})
    assert response.status_code == 200
    lines = audit_path.read_text("utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["route"] == "/retrieve"
    assert record["corpus"] == "synthetic"
    assert record["query"] == GREEN_QUERY
    assert record["status_code"] == 200
    assert record["request_id"] == response.headers["X-Request-ID"]


def test_health_is_not_audited(tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.jsonl"
    client = make_client(audit_log_path=audit_path)
    client.get("/health")
    assert not audit_path.exists()
