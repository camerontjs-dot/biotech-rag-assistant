"""Shared helpers for the chat prototype tests (imported by tests/test_chat_*.py)."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from biotech_rag_assistant.api.config import ApiConfig
from biotech_rag_assistant.chat.app import create_chat_app
from biotech_rag_assistant.chat.evidence import CorpusBinding
from biotech_rag_assistant.chat.provider import ChatProvider
from biotech_rag_assistant.chat.settings import ChatSettings
from biotech_rag_assistant.chat.testing import answer, block, find_passage, request_payload
from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import build_retriever

ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "examples/synthetic-controlled-docs"
ADVERSARIAL_CORPUS = ROOT / "tests/fixtures/chat-adversarial"
LOADED_AT = datetime(2026, 11, 4, tzinfo=UTC)

EM_QUESTION = "How does QA respond to a viable environmental monitoring excursion?"
BALANCE_QUESTION = "What is the acceptance range for the analytical balance daily check?"
LINE_CLEARANCE_QUESTION = "Who must sign the line clearance record before the run starts?"
OBSOLETE_TRAP = "What is the membrane filtration hold time for sterility?"
LABELS_QUESTION = "How are printed sample labels reconciled before testing?"


def binding_for(path: Path = DEMO_CORPUS, name: str = "synthetic") -> CorpusBinding:
    corpus = load_corpus(path)
    return CorpusBinding.build(name, corpus, build_retriever(corpus.documents), LOADED_AT)


def make_client(
    provider: ChatProvider | None = None,
    *,
    corpus: Path = DEMO_CORPUS,
    name: str = "synthetic",
    settings: ChatSettings | None = None,
    env: dict[str, str] | None = None,
    **config_overrides: Any,
) -> TestClient:
    config = ApiConfig(corpora={name: corpus}, default_corpus=name, **config_overrides)
    app = create_chat_app(config, settings or ChatSettings(), provider, env=env or {})
    return TestClient(app)


def ask(client: TestClient, message: str, session_id: str | None = None, **extra: Any) -> dict:
    body: dict[str, Any] = {"message": message, **extra}
    if session_id is not None:
        body["session_id"] = session_id
    response = client.post("/chat", json=body)
    assert response.status_code == 200, response.text
    return response.json()


def quoting(
    doc_id: str,
    contains: str,
    text: str,
    quote: str | None = None,
    *,
    status: str = "answered",
    kind: str = "paragraph",
) -> Callable[[Any, dict[str, Any]], dict[str, Any]]:
    """Scripted step: one block citing the supplied ``doc_id`` passage that has ``contains``."""

    def step(request: Any, payload: dict[str, Any]) -> dict[str, Any]:
        ref = find_passage(payload, doc_id=doc_id, contains=contains)["ref"]
        return answer(status, [block(kind, text, (ref, quote or contains))])

    return step


def all_input_text(request: Any) -> str:
    return "\n".join(message["content"] for message in request.input)


def history_text(request: Any) -> str:
    """Everything sent to the model except the final (current-turn) payload message."""
    return "\n".join(message["content"] for message in request.input[:-1])


def passages_text(request: Any) -> str:
    return json.dumps(request_payload(request)["passages"], ensure_ascii=False)
