"""Exercise the native ep1 identity contract offline; do not grade support.

Build a packet from the synthetic demo through the real corpus, BM25, and
admission code. Mutate only heading metadata, then prepare (never send) a
request. Preserve full before/after records and identity-bearing controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path

from biotech_rag_assistant.corpus import CorpusValidationError, load_corpus
from biotech_rag_assistant.evidence_packet import (
    EvidencePacket,
    build_evidence_packet,
    canonical_json,
    expected_packet_id,
    packet_identity_valid,
)
from biotech_rag_assistant.ollama_generator import OllamaGenerator
from biotech_rag_assistant.retrieval import RetrievalConfig, run_retrieval

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "examples/synthetic-controlled-docs"
QUERY = "balance traceable weights"
MUTATED_HEADING = "Weekly check"
IDENTITY_FIELDS = (
    "chunk_id", "doc_id", "version", "status", "source_hash",
    "char_start", "char_end", "nomination_kind",
)


def forbidden_transport(url: str, body: bytes, timeout: float) -> bytes:
    raise RuntimeError("Transport is forbidden in the offline identity check")


def fixture_packet(repository: Path = ROOT) -> EvidencePacket:
    corpus = load_corpus(repository / FIXTURE)
    config = RetrievalConfig(top_k=1)
    hits = run_retrieval(corpus.documents, QUERY, config)
    packet = build_evidence_packet(corpus, QUERY, hits, config)
    if not packet_identity_valid(packet) or len(packet.admitted_nominations) != 1:
        raise ValueError("Native fixture did not produce one valid admitted nomination")
    nomination = packet.admitted_nominations[0]
    if nomination.chunk_id != "CAL-ENG-005_v1_0_chunk_001":
        raise ValueError("Native fixture nominated an unexpected source span")
    return packet


def mutate_nomination(packet: EvidencePacket, field: str, value: object) -> EvidencePacket:
    record = packet.to_record()
    record["admitted_nominations"][0][field] = value
    return EvidencePacket.model_validate(record)


def observe_identity(repository: Path = ROOT) -> dict:
    original = fixture_packet(repository)
    heading = original.admitted_nominations[0].section_heading
    if heading != "Daily check":
        raise ValueError("Native source heading changed")
    changed = mutate_nomination(original, "section_heading", MUTATED_HEADING)
    before = original.admitted_nominations[0].model_dump()
    after = changed.admitted_nominations[0].model_dump()
    changed_fields = [key for key in before if before[key] != after[key]]
    if changed_fields != ["section_heading"]:
        raise ValueError("Mutation changed more than heading metadata")

    # This prepares a payload with the real adapter. It never calls generate,
    # generate_with_receipt, a transport, or any provider endpoint.
    adapter = OllamaGenerator(model_id="gemma3:12b", transport=forbidden_transport)
    payload = adapter.request_payload(changed)
    payload_accepts_heading = f'"section_heading":"{MUTATED_HEADING}"' in payload["prompt"]

    span_changed = mutate_nomination(original, "char_end", before["char_end"] + 1)
    query_record = original.to_record()
    query_record["query"] += " altered"
    query_changed = EvidencePacket.model_validate(query_record)
    text_changed = mutate_nomination(original, "text", before["text"] + " Altered body.")
    controls = {
        "body_span_changed_packet_valid": packet_identity_valid(span_changed),
        "query_changed_packet_valid": packet_identity_valid(query_changed),
        "body_text_only_changed_packet_valid": packet_identity_valid(text_changed),
    }
    observed = {
        "original_packet_valid": packet_identity_valid(original),
        "heading_changed_packet_valid": packet_identity_valid(changed),
        "declared_packet_id_unchanged": changed.packet_id == original.packet_id,
        "recomputed_packet_id_unchanged": expected_packet_id(changed) == original.packet_id,
        "nomination_identity_tuple_unchanged": (
            original.admitted_nominations[0].identity_tuple()
            == changed.admitted_nominations[0].identity_tuple()
        ),
        "identity_bearing_fields_unchanged": all(before[k] == after[k] for k in IDENTITY_FIELDS),
        "changed_nomination_fields": changed_fields,
        "adapter_request_preparation_accepts_changed_heading": payload_accepts_heading,
        "adapter_generate_call_count": adapter.call_count,
    }
    expected = all(observed[k] for k in (
        "original_packet_valid", "heading_changed_packet_valid",
        "declared_packet_id_unchanged", "recomputed_packet_id_unchanged",
        "nomination_identity_tuple_unchanged", "identity_bearing_fields_unchanged",
        "adapter_request_preparation_accepts_changed_heading",
    )) and adapter.call_count == 0 and controls == {
        "body_span_changed_packet_valid": False,
        "query_changed_packet_valid": False,
        "body_text_only_changed_packet_valid": True,
    }
    authority_paths = (
        "src/biotech_rag_assistant/evidence_packet.py",
        "src/biotech_rag_assistant/generation.py",
        "src/biotech_rag_assistant/ollama_generator.py",
        "src/biotech_rag_assistant/chunking.py",
        "src/biotech_rag_assistant/corpus.py",
        "src/biotech_rag_assistant/retrieval.py",
        FIXTURE + "/documents/CAL-ENG-005-balance-calibration.md",
    )
    return {
        "schema_version": "ep1-heading-identity-observation/v1",
        "status": "PASS_IDENTITY_CONTRACT_OBSERVATION" if expected else "IDENTITY_CONTRACT_CHANGED",
        "fixture": FIXTURE,
        "python_version": platform.python_version(),
        "authority_sha256": {
            name: hashlib.sha256((repository / name).read_bytes()).hexdigest()
            for name in authority_paths
        },
        "original_packet": original.to_record(),
        "heading_mutated_packet": changed.to_record(),
        "observation": observed,
        "controls": controls,
        "prepared_request_sha256": hashlib.sha256(canonical_json(payload)).hexdigest(),
        "limitation": (
            "ep1 validates declared source identities, not every model-visible byte; "
            "body text also lies outside the direct tuple."
        ),
        "semantic_authority_decided_by_checker": False,
        "new_model_calls": 0,
        "provider_transport_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = observe_identity()
    except (CorpusValidationError, OSError, ValueError, TypeError) as exc:
        # No substitute packet or successful observation on fixture failure.
        result = {"status": "APPARATUS_FAILURE", "error_type": type(exc).__name__}
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    return 0 if result["status"] == "PASS_IDENTITY_CONTRACT_OBSERVATION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
