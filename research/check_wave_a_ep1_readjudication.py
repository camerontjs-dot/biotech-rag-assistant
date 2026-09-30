"""Verify exact offline successor bindings; do not decide semantic support.

The six classifications are qualitative agent judgments. This helper checks
their evidence and claim bindings, never their semantic truth or preferred value.
It reads only the preserved Wave A allowlist and native synthetic corpus.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.evidence_packet import EvidencePacket
from research.check_wave_a_support_aperture_evidence import check_evidence, require

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/evidence/wave-a-ep1-authority-readjudication-v1"
ORIGINAL = ROOT / "research/evidence/wave-a-support-aperture-v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def record(path: Path) -> dict:
    return json.loads(path.read_bytes())


def check_bindings(evidence: Path = EVIDENCE) -> dict:
    experiment = record(evidence / "EXPERIMENT.json")
    result = record(evidence / "adjudication.json")
    surfaces = record(evidence / "support-surfaces.json")
    custody = record(evidence / "custody-check.json")
    require(check_evidence(ORIGINAL) == custody, "custody receipt drift")
    require(digest(ORIGINAL / "evidence-manifest.json") ==
            experiment["input_evidence_manifest_sha256"], "evidence manifest drift")
    for name, pin in experiment["input_sha256"].items():
        require(digest(ORIGINAL / name) == pin, f"original file drift: {name}")
    for name, pin in experiment["receipt_sha256"].items():
        require(digest(evidence / name) == pin, f"successor receipt drift: {name}")
    require(digest(ROOT / experiment["protocol"]["path"]) ==
            experiment["protocol"]["sha256"], "preregistered protocol drift")
    require(digest(ROOT / "DECISIONS.md") ==
            experiment["authority"]["decisions_sha256"], "accepted authority drift")
    require(digest(ORIGINAL / "adjudication.json") ==
            experiment["predecessor"]["adjudication_sha256"], "historical result drift")
    inputs = {row["case_id"]: row for row in (
        json.loads(line) for line in
        (ORIGINAL / "frozen/bundle/wave-a-probes.jsonl").read_bytes().splitlines()
    )}
    projections = {row["case_id"]: row for row in surfaces["observations"]}
    observations = {row["case_id"]: row for row in custody["observations"]}
    corpus = load_corpus(ROOT / "examples/synthetic-controlled-docs")
    sources = {doc.metadata.doc_id: doc for doc in corpus.documents}
    require(sorted(row["case_id"] for row in result["cases"]) ==
            sorted(observations), "successor case identity/count drift")
    checks = []
    for case in result["cases"]:
        case_id = case["case_id"]
        projected = projections[case_id]
        original = observations[case_id]
        claim = case["exact_generated_claim"]
        require(claim == original["exact_claim"] == projected["exact_generated_claim"],
                f"claim drift: {case_id}")
        require(case["question"] == inputs[case_id]["question"] == projected["question"],
                f"question drift: {case_id}")
        require(case["packet_id"] == original["packet_id"] == projected["packet_id"],
                f"packet drift: {case_id}")
        packet = EvidencePacket.model_validate(inputs[case_id]["packet"])
        require(len(projected["P"]) == len(packet.admitted_nominations),
                f"packet body count drift: {case_id}")
        for span, nomination in zip(projected["P"], packet.admitted_nominations, strict=True):
            expected = {
                key: getattr(nomination, key) for key in
                ("text", "chunk_id", "doc_id", "source_hash", "char_start", "char_end")
            }
            require(span == {**expected, "source_span_verified": True},
                    f"packet body projection drift: {case_id}")
            source = sources[nomination.doc_id]
            require(source.raw_text[nomination.char_start:nomination.char_end] ==
                    nomination.text and source.computed_source_hash == nomination.source_hash,
                    f"source span drift: {case_id}")
        citation = claim["citations"][0]
        cited_body = next(span for span in projected["P"]
                          if span["chunk_id"] == citation["chunk_id"])
        require(projected["N"] == [cited_body], f"nomination projection drift: {case_id}")
        require(projected["Q"] == [{"chunk_id": citation["chunk_id"],
                                    "text": citation["quote"]}],
                f"quote projection drift: {case_id}")
        require(set(case["apertures"]) == {"Q", "N", "P"}, "aperture count drift")
        for name, aperture in case["apertures"].items():
            require(aperture["evidence_used"] == projected[name] and
                    aperture["exact_claim_text"] == claim["text"] and
                    aperture["exact_citation"] == citation,
                    f"judgment binding drift: {case_id}/{name}")
            require(aperture["classification"] in
                    {"SUPPORTED", "OVER_BROAD", "UNSUPPORTED", "INCONCLUSIVE"},
                    "invalid classification label")
            require(aperture["evaluator"] == "agent_llm" and
                    aperture["independent_human_adjudication"] is False,
                    "incorrect evaluator attribution")
            checks.append({"case_id": case_id, "aperture": name, "exact_binding": "PASS"})
    return {
        "schema_version": "wave-a-ep1-authority-artifact-verification/v1",
        "status": "PASS_EXACT_OFFLINE_ARTIFACT_BINDINGS",
        "verified_original_file_count": len(experiment["input_sha256"]),
        "verified_packet_body_spans": sum(len(row["P"]) for row in projections.values()),
        "verified_judgment_bindings": checks,
        "protocol_sha256": experiment["protocol"]["sha256"],
        "adjudication_sha256": digest(evidence / "adjudication.json"),
        "checker_sha256": digest(Path(__file__)),
        "semantic_classifications": "NOT_DETERMINED_BY_THIS_CHECK",
        "new_model_calls": 0,
        "generation_or_gate_replays": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_bindings()
    except (OSError, KeyError, ValueError, TypeError, StopIteration) as exc:
        result = {"status": "FAIL_EXACT_OFFLINE_ARTIFACT_BINDINGS", "error": str(exc)}
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    return 0 if result["status"] == "PASS_EXACT_OFFLINE_ARTIFACT_BINDINGS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
