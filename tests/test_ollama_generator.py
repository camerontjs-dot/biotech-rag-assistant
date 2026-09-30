from __future__ import annotations

import json
from pathlib import Path

import pytest

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import (
    EvidenceBudget,
    build_evidence_packet,
)
from biotech_rag_assistant.generation import GeneratedAnswer
from biotech_rag_assistant.ollama_generator import (
    OllamaGenerator,
    SHADOW_GENERATION_PROMPT_SHA256,
)
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "examples/synthetic-controlled-docs"
QUERY = "viable excursion affected product lots immediate containment"
EXPECTED_PROMPT_SHA256 = (
    "d1cd4cb7c727207b354552d0668a9d922967b87bd8615da5994c88aa0c2c8447"
)


def make_packet():
    corpus = load_corpus(CORPUS_DIR)
    config = RetrievalConfig(top_k=3)
    hits = run_retrieval(corpus.documents, QUERY, config)
    return build_evidence_packet(
        corpus,
        QUERY,
        hits,
        config,
        budget=EvidenceBudget(max_items=3, max_context_chars=12_000),
    )


def test_prompt_hash_remains_frozen() -> None:
    assert SHADOW_GENERATION_PROMPT_SHA256 == EXPECTED_PROMPT_SHA256


def test_ollama_payload_uses_exact_generated_answer_schema() -> None:
    packet = make_packet()
    generator = OllamaGenerator(model_id="gemma3:12b")

    payload = generator.request_payload(packet)

    assert payload["model"] == "gemma3:12b"
    assert payload["stream"] is False
    assert payload["raw"] is True
    assert payload["keep_alive"] == 0
    assert payload["format"] == GeneratedAnswer.model_json_schema()
    assert payload["options"] == {
        "temperature": 0.0,
        "seed": 42,
        "num_ctx": 32768,
        "num_predict": 4096,
        "top_k": 40,
        "top_p": 1.0,
        "min_p": 0.0,
        "repeat_penalty": 1.0,
    }
    assert payload["prompt"].endswith(
        json.dumps(
            packet.to_record(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    assert generator.prompt_hash == f"sha256:{EXPECTED_PROMPT_SHA256}"


def test_generate_with_receipt_preserves_raw_provider_body_and_parses_json() -> None:
    packet = make_packet()
    calls: list[tuple[str, bytes, float]] = []
    raw = json.dumps(
        {
            "model": "gemma3:12b",
            "response": json.dumps(
                {
                    "disposition": "not_stated",
                    "claims": [],
                    "gaps": [
                        {
                            "asked_about": "the requested numeric limit",
                            "statement": "The topic is present but the limit is not stated.",
                            "topic_citation": {
                                "chunk_id": packet.admitted_nominations[0].chunk_id,
                                "quote": packet.admitted_nominations[0].text,
                            },
                        }
                    ],
                }
            ),
            "done": True,
        },
        separators=(",", ":"),
    ).encode("utf-8")

    def fake_transport(url: str, body: bytes, timeout: float) -> bytes:
        calls.append((url, body, timeout))
        return raw

    generator = OllamaGenerator(
        model_id="gemma3:12b",
        transport=fake_transport,
    )
    receipt = generator.generate_with_receipt(packet)

    assert generator.call_count == 1
    assert len(calls) == 1
    assert calls[0][0] == "http://127.0.0.1:11434/api/generate"
    sent = json.loads(calls[0][1])
    assert sent["format"] == GeneratedAnswer.model_json_schema()
    assert receipt.raw_http_body == raw
    assert receipt.envelope["done"] is True
    assert isinstance(receipt.parsed_output, dict)
    assert receipt.parsed_output["disposition"] == "not_stated"


def test_non_json_model_text_is_preserved_for_g1_instead_of_repaired() -> None:
    packet = make_packet()
    provider_text = "\`\`\`json\n{\\"disposition\\":\\"answered\\"}\n\`\`\`"
    raw = json.dumps(
        {
            "model": "gemma3:12b",
            "response": provider_text,
            "done": True,
        }
    ).encode("utf-8")

    generator = OllamaGenerator(
        model_id="gemma3:12b",
        transport=lambda _url, _body, _timeout: raw,
    )
    receipt = generator.generate_with_receipt(packet)

    assert receipt.response_text == provider_text
    assert receipt.parsed_output == provider_text


def test_invalid_packet_identity_blocks_transport_call() -> None:
    packet = make_packet().model_copy(
        update={"query": "tampered after packet identity"}
    )
    calls = 0

    def fake_transport(_url: str, _body: bytes, _timeout: float) -> bytes:
        nonlocal calls
        calls += 1
        raise AssertionError("transport must not be called")

    generator = OllamaGenerator(
        model_id="gemma3:12b",
        transport=fake_transport,
    )

    with pytest.raises(ValueError, match="packet identity is invalid"):
        generator.generate_with_receipt(packet)

    assert calls == 0
    assert generator.call_count == 0
