"""Check preserved Wave A custody and bindings offline; do not adjudicate semantics.

This checker reads an explicit allowlist, verifies hashes, and compares first-run
values. It never calls a generator, reruns G1-G7, or selects a support aperture.
Qualitative classifications live separately in adjudication.json (agent_llm).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from biotech_rag_assistant.evidence_packet import EvidencePacket, packet_identity_valid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "research/evidence/wave-a-support-aperture-v1"
CASE_IDS = ("A07-balance-weight-count", "A08-line-clearance-signatories")
FROZEN_FILES = {
    "generation-freeze.json",
    "replay-freeze.json",
    "bundle/manifest.json",
    "bundle/wave-a-probes.jsonl",
    "structured-run/outputs.jsonl",
    "structured-run/run_metadata.json",
    "structured-run/raw-manifest.json",
    "structured-replay/wave-a-gated-results.json",
    *(f"structured-run/raw/{case_id}.json" for case_id in CASE_IDS),
}
ALLOWED_FILES = {*(f"frozen/{name}" for name in FROZEN_FILES),
                 "original-receipt-projection.json"}
ANCHOR_HASHES = {
    "frozen/generation-freeze.json":
        "046cc15ecd58b5667599e4b83c4e7331f3bff3ff950a80e8615e0ffc37d81bd5",
    "frozen/replay-freeze.json":
        "0ef347bc5d727fd8e06ef3ea8e050279a51cf07fed9bada2f341a9842226a664",
    "frozen/bundle/manifest.json":
        "80a582477de420bbf4655a8936be6067fd8cad85df2ea21f61fec6efc1945903",
}
AUTHORITY_PATHS = {
    "DECISIONS.md",
    "src/biotech_rag_assistant/generation.py",
    "src/biotech_rag_assistant/evidence_packet.py",
    "src/biotech_rag_assistant/chunking.py",
    "src/biotech_rag_assistant/models.py",
    "src/biotech_rag_assistant/retrieval.py",
    "src/biotech_rag_assistant/ollama_generator.py",
    "tests/test_chunking.py",
    "tests/test_evidence_packet.py",
    "tests/test_generation_gates.py",
    "research/evidence-packet-v1-protocol.md",
    "research/generation-claim-gates-v1-protocol.md",
    "research/wave-a-support-aperture-adjudication-protocol.md",
    "examples/synthetic-controlled-docs/documents/CAL-ENG-005-balance-calibration.md",
    "examples/synthetic-controlled-docs/documents/SOP-OPS-007-line-clearance.md",
}


class EvidenceError(ValueError):
    """Incomplete, changed, or inconsistent preserved evidence."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_rows(rows: list[dict]) -> dict[str, dict]:
    keyed = {row["case_id"]: row for row in rows}
    require(len(keyed) == len(rows), "duplicate case identity")
    return keyed


def check_evidence(evidence: Path, repository: Path = ROOT) -> dict:
    manifest_bytes = (evidence / "evidence-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    require(set(manifest["files"]) == ALLOWED_FILES, "evidence file allowlist mismatch")
    require(set(manifest["repository_authority_sha256"]) == AUTHORITY_PATHS,
            "repository authority allowlist mismatch")
    # Reject unexpected paths before reading any path supplied by a manifest.
    blobs = {}
    for name, pin in manifest["files"].items():
        path = evidence / name
        require(not path.is_symlink(), f"symlink evidence: {name}")
        data = path.read_bytes()
        digest = sha256(data)
        require(digest == pin["sha256"] and len(data) == pin["bytes"],
                f"preserved hash mismatch: {name}")
        if name in ANCHOR_HASHES:
            require(digest == ANCHOR_HASHES[name], f"first-run anchor mismatch: {name}")
        blobs[name] = data
    for name, pin in manifest["repository_authority_sha256"].items():
        require(sha256((repository / name).read_bytes()) == pin,
                f"repository authority drift: {name}")

    def record(name: str) -> dict:
        return json.loads(blobs[f"frozen/{name}"])

    for freeze, field in (("generation-freeze.json", "generation_artifacts"),
                          ("replay-freeze.json", "replay_artifacts")):
        pins = record(freeze)[field]
        for name, data in blobs.items():
            relative = name.removeprefix("frozen/")
            if relative in pins:
                require(sha256(data) == pins[relative]["sha256"],
                        f"original freeze binding mismatch: {relative}")

    bundle = record("bundle/manifest.json")
    metadata = record("structured-run/run_metadata.json")
    wave_a = blobs["frozen/bundle/wave-a-probes.jsonl"]
    require(sha256(wave_a) == bundle["files"]["wave-a-probes.jsonl"]
            == metadata["wave_a_sha256"], "first-run Wave A input binding mismatch")
    inputs = unique_rows([json.loads(line) for line in wave_a.splitlines()])
    outputs = unique_rows([json.loads(line) for line in
                           blobs["frozen/structured-run/outputs.jsonl"].splitlines()])
    replay = record("structured-replay/wave-a-gated-results.json")
    results = unique_rows(replay["results"])
    raw_manifest = record("structured-run/raw-manifest.json")
    projection = json.loads(blobs["original-receipt-projection.json"])
    require(projection["call_accounting"]["actual_model_calls"] == 6,
            "first-run call count changed")
    observations = []
    for case_id in CASE_IDS:
        packet = EvidencePacket.model_validate(inputs[case_id]["packet"])
        require(packet_identity_valid(packet), f"invalid frozen packet identity: {case_id}")
        raw_name = f"structured-run/raw/{case_id}.json"
        raw = record(raw_name)
        require(sha256(blobs[f"frozen/{raw_name}"])
                == raw_manifest["raw_response_sha256"][case_id],
                f"raw-manifest binding mismatch: {case_id}")
        require(raw["model"] == "gemma3:12b" and raw["done"] is True
                and raw["done_reason"] == "stop", f"nonterminal/wrong provider: {case_id}")
        payload = json.loads(raw["response"])
        require(payload == outputs[case_id]["raw_output"], f"provider/output mismatch: {case_id}")
        result = results[case_id]
        require(payload["claims"] == result["accepted_claims"]
                and len(result["accepted_claims"]) == 1,
                f"frozen accepted claim mismatch: {case_id}")
        require(result["packet_id"] == packet.packet_id
                and result["question"] == inputs[case_id]["question"] == packet.query,
                f"packet/replay/question mismatch: {case_id}")
        claim = result["accepted_claims"][0]
        require(len(claim["citations"]) == 1, f"changed citation count: {case_id}")
        citation = claim["citations"][0]
        cited = [n for n in packet.admitted_nominations if n.chunk_id == citation["chunk_id"]]
        require(len(cited) == 1, f"ambiguous cited nomination: {case_id}")
        nomination = cited[0]
        require(citation["quote"] in nomination.text, f"quote/body mismatch: {case_id}")
        source_name = {
            "CAL-ENG-005": "CAL-ENG-005-balance-calibration.md",
            "SOP-OPS-007": "SOP-OPS-007-line-clearance.md",
        }[nomination.doc_id]
        source_path = "examples/synthetic-controlled-docs/documents/" + source_name
        source_bytes = (repository / source_path).read_bytes()
        source_text = source_bytes.decode("utf-8")
        require("sha256:" + sha256(source_bytes) == nomination.source_hash,
                f"source hash mismatch: {case_id}")
        require(source_text[nomination.char_start:nomination.char_end] == nomination.text,
                f"source span mismatch: {case_id}")
        preceding = source_text[:nomination.char_start].splitlines()
        headings = [line.lstrip("#").strip() for line in preceding if line.startswith("#")]
        require(headings[-1] == nomination.section_heading,
                f"heading provenance mismatch: {case_id}")
        observations.append({
            "case_id": case_id, "packet_id": packet.packet_id,
            "exact_claim": claim, "exact_cited_nomination": nomination.model_dump(),
            "public_disposition": result["public_disposition"],
            "source_text_and_heading_provenance_match": True,
            "semantic_authority_decided_by_checker": False,
        })
    return {
        "schema_version": "wave-a-support-aperture-custody-check/v1",
        "status": "PASS_PRESERVED_EVIDENCE_BINDINGS",
        "evidence_manifest_sha256": sha256(manifest_bytes),
        "verified_preserved_file_count": len(blobs),
        "new_model_calls": 0, "generation_or_gate_replays": 0,
        "semantic_adjudication": "NOT_PERFORMED_BY_CHECKER",
        "observations": observations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_evidence(args.evidence)
    except (OSError, KeyError, ValueError, TypeError) as exc:
        result = {"status": "FAIL_PRESERVED_EVIDENCE_BINDINGS", "error": str(exc)}
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    return 0 if result["status"] == "PASS_PRESERVED_EVIDENCE_BINDINGS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
