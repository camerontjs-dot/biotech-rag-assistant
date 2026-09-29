#!/usr/bin/env python3
"""Emit one fixed EvidencePacket identity receipt for cross-Python comparison."""
from __future__ import annotations

import json
import platform
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import EvidenceBudget, build_evidence_packet
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "examples/synthetic-controlled-docs"
QUERY = "viable excursion affected product lots immediate containment"


def main() -> int:
    corpus = load_corpus(CORPUS)
    config = RetrievalConfig(top_k=3)
    hits = run_retrieval(corpus.documents, QUERY, config)
    packet = build_evidence_packet(
        corpus,
        QUERY,
        hits,
        config,
        budget=EvidenceBudget(
            max_items=3,
            max_context_chars=12_000,
            expand_sections=False,
        ),
    )
    print(
        json.dumps(
            {
                "python": platform.python_version(),
                "packet_id": packet.packet_id,
                "query_id": packet.query_id,
                "corpus_identity": packet.corpus_identity,
                "retrieval_config_id": packet.retrieval_config_id,
                "admitted_chunk_ids": [
                    item.chunk_id for item in packet.admitted_nominations
                ],
                "exclusion_summary": packet.exclusion_summary,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
