"""Tests for the demo web UI composed over the pure transport app.

The demo app adds a static chat page at ``GET /`` but must not change the transport
contract: the same status gate, citation validation, and refusal behavior still apply.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.api.webui import create_demo_app

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"


def make_client() -> TestClient:
    config = ApiConfig(corpora={"synthetic": DEMO_CORPUS}, default_corpus="synthetic")
    return TestClient(create_demo_app(config))


def test_root_serves_the_demo_page() -> None:
    response = make_client().get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Biotech RAG Assistant" in response.text
    assert "What this is not" in response.text


def test_demo_app_keeps_answer_contract() -> None:
    client = make_client()

    answered = client.post(
        "/answer",
        json={"query": "How does QA respond to a viable environmental monitoring excursion?"},
    ).json()
    assert answered["outcome"] == "answer"
    assert answered["citation_validation"]["valid"] is True

    refused = client.post(
        "/answer",
        json={"query": "What is the company vacation policy and paid days off?"},
    ).json()
    assert refused["outcome"] == "refusal"
    assert refused["review_recommendation"]["review_recommended"] is True


def test_health_still_present_on_demo_app() -> None:
    response = make_client().get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
