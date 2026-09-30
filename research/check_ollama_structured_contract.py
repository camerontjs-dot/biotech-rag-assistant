#!/usr/bin/env python3
"""Emit a no-network receipt for the schema-constrained Ollama adapter contract."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import (
    EvidenceBudget,
    build_evidence_packet,
)
from biotech_rag_assistant.generation import synthesize_shadow
from biotech_rag_assistant.ollama_generator import (
    OllamaGenerator,
    SHADOW_GENERATION_PROMPT_SHA256,
)
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "examples/synthetic-controlled-docs"
QUERY = "viable excursion affected product lots immediate containment"


def main() -> int:
    corpus = load_corpus(CORPUS_DIR)
    config = RetrievalConfig(top_k=3)
    hits = run_retrieval(corpus.documents, QUERY, config)
    packet = build_evidence_packet(
        corpus,
        QUERY,
        hits,
        config,
        budget=EvidenceBudget(max_items=3, max_context_chars=12_000),
    )
    cited = packet.admitted_nominations[0]
    provider_object = {
        "model": "gemma3:12b",
        "response": json.dumps(
            {
                "disposition": "answered",
                "claims": [
                    {
                        "claim_id": "c1",
                        "text": cited.text,
                        "citations": [
                            {
                                "chunk_id": cited.chunk_id,
                                "quote": cited.text,
                            }
                        ],
                        "qualifier": None,
                        "limitation": None,
                    }
                ],
                "gaps": [],
            },
            separators=(",", ":"),
        ),
        "done": True,
    }
    raw_provider = json.dumps(
        provider_object,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    captured: list[dict] = []

    def fake_transport(url: str, body: bytes, timeout: float) -> bytes:
        captured.append(
            {
                "url": url,
                "payload": json.loads(body),
                "timeout": timeout,
            }
        )
        return raw_provider

    generator = OllamaGenerator(
        model_id="gemma3:12b",
        transport=fake_transport,
    )
    result = synthesize_shadow(packet, generator)

    if result.disposition != "generated":
        raise SystemExit(
            f"expected generated control, observed {result.disposition}"
        )
    if generator.call_count != 1 or len(captured) != 1:
        raise SystemExit("adapter did not make exactly one provider call")

    payload = captured[0]["payload"]
    schema_bytes = json.dumps(
        payload["format"],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    report = {
        "disposition": "PASS_OLLAMA_STRUCTURED_ADAPTER_CONTRACT",
        "packet_id": packet.packet_id,
        "prompt_sha256": SHADOW_GENERATION_PROMPT_SHA256,
        "generated_answer_schema_sha256": hashlib.sha256(
            schema_bytes
        ).hexdigest(),
        "request": {
            "url": captured[0]["url"],
            "model": payload["model"],
            "stream": payload["stream"],
            "raw": payload["raw"],
            "keep_alive": payload["keep_alive"],
            "options": payload["options"],
            "schema_additional_properties": payload["format"].get(
                "additionalProperties"
            ),
        },
        "raw_provider_body_sha256": hashlib.sha256(
            raw_provider
        ).hexdigest(),
        "generator_call_count": generator.call_count,
        "public_disposition": result.disposition,
        "accepted_claim_count": len(result.accepted_claims),
        "issue_gates": sorted({issue.gate for issue in result.issues}),
        "network_used": False,
        "non_claims": [
            "This receipt uses a fake transport and makes no Ollama network call.",
            "It qualifies request construction and adapter-to-gate composition only.",
            "It does not establish live-model output quality.",
        ],
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
