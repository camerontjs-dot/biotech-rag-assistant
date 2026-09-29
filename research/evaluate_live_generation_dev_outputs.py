#!/usr/bin/env python3
"""Replay local DEV live-generation outputs through the exact G1-G7 gate engine."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from biotech_rag_assistant.evidence_packet import EvidencePacket
from biotech_rag_assistant.generation import ScriptedGenerator, synthesize_shadow

WAVE_A_EXPECTED = {
    "A01-balance-acceptance-range": "not_stated",
    "A02-gowning-absence": "not_stated",
    "A03-controlled-copy-use-period": "not_stated",
    "A04-em-action-limit": "not_stated",
    "A05-deviation-close-days": "refusal",
    "A06-purified-water-action-limit": "refusal",
    "A07-balance-weight-count": "generated",
    "A08-line-clearance-signatories": "generated",
    "A09-obsolete-membrane-hold": "refusal",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_outputs(path: Path) -> tuple[dict[str, object], list[str]]:
    rows = jsonl(path)
    outputs: dict[str, object] = {}
    errors: list[str] = []
    for row in rows:
        if set(row) != {"case_id", "raw_output"}:
            errors.append(
                "output rows must contain exactly case_id and raw_output"
            )
            continue
        case_id = row["case_id"]
        if case_id in outputs:
            errors.append(f"duplicate output row for {case_id}")
            continue
        outputs[case_id] = row["raw_output"]
    return outputs, errors


def verify_bundle(
    bundle: Path,
    *,
    wave: str,
) -> tuple[dict, str, list[str]]:
    """Verify only authority needed for the selected wave.

    The manifest itself is always read and hashed. For wave A, Wave B is not
    opened, hashed, parsed, or required to exist. The inverse holds for wave B.
    """
    errors: list[str] = []
    manifest_path = bundle / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_wave = (
        "wave-a-probes.jsonl"
        if wave == "a"
        else "wave-b-v21-dev.jsonl"
    )
    for name in ("prompt.txt", selected_wave):
        expected = manifest["files"].get(name)
        if expected is None:
            errors.append(f"manifest missing selected bundle file: {name}")
            continue
        path = bundle / name
        if not path.exists():
            errors.append(f"missing selected bundle file: {name}")
            continue
        observed = sha256(path)
        if observed != expected:
            errors.append(
                f"bundle hash mismatch for {name}: {observed} != {expected}"
            )
    manifest_hash = sha256(manifest_path)
    return manifest, manifest_hash, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, required=True)
    parser.add_argument("--run-metadata", type=Path, required=True)
    parser.add_argument(
        "--wave",
        choices=("a", "b"),
        required=True,
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    bundle = args.bundle.resolve()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest, manifest_hash, errors = verify_bundle(
        bundle,
        wave=args.wave,
    )
    prompt_text = (bundle / "prompt.txt").read_text(encoding="utf-8")
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()

    metadata = json.loads(
        args.run_metadata.read_text(encoding="utf-8")
    )
    required_metadata = {
        "provider",
        "model_id",
        "parameters_or_effort",
        "prompt_sha256",
        "bundle_manifest_sha256",
        "isolation_notes",
        "fresh_context_policy",
    }
    missing = required_metadata - set(metadata)
    if missing:
        errors.append(f"run metadata missing fields: {sorted(missing)}")
    if metadata.get("prompt_sha256") != prompt_hash:
        errors.append("run metadata prompt hash does not match bundle")
    if metadata.get("bundle_manifest_sha256") != manifest_hash:
        errors.append("run metadata bundle manifest hash does not match")

    outputs, output_errors = load_outputs(args.outputs)
    errors.extend(output_errors)

    filename = (
        "wave-a-probes.jsonl"
        if args.wave == "a"
        else "wave-b-v21-dev.jsonl"
    )
    cases = jsonl(bundle / filename)
    case_ids = {row["case_id"] for row in cases}
    extras = sorted(set(outputs) - case_ids)
    if extras:
        errors.append(f"outputs contain unknown case IDs: {extras}")

    results: list[dict] = []
    issue_counts: Counter[str] = Counter()
    fallback_counts: Counter[str] = Counter()
    human_review: list[dict] = []
    disposition_matches = 0

    for row in cases:
        case_id = row["case_id"]
        packet = EvidencePacket.model_validate(row["packet"])
        should_call = bool(row["generator_should_be_called"])
        has_output = case_id in outputs

        if should_call and not has_output:
            errors.append(f"missing model output for callable case {case_id}")
            continue
        if not should_call and has_output:
            errors.append(
                f"model output supplied for empty-packet case {case_id}"
            )
            continue

        if should_call:
            generator = ScriptedGenerator(
                outputs[case_id],
                model_id=str(metadata.get("model_id", "unknown")),
                prompt_text=prompt_text,
            )
        else:
            generator = ScriptedGenerator(
                {
                    "disposition": "answered",
                    "claims": [],
                    "gaps": [],
                },
                model_id=str(metadata.get("model_id", "unknown")),
                prompt_text=prompt_text,
            )

        gated = synthesize_shadow(packet, generator)
        gates = sorted({issue.gate for issue in gated.issues})
        for gate in gates:
            issue_counts[gate] += 1
        if gated.fallback_reason:
            fallback_counts[gated.fallback_reason] += 1

        record = {
            "case_id": case_id,
            "question": row["question"],
            "packet_id": packet.packet_id,
            "generator_should_be_called": should_call,
            "generator_called_by_gate_wrapper": gated.generator_called,
            "public_disposition": gated.disposition,
            "outcome": gated.outcome,
            "accepted_claim_count": len(gated.accepted_claims),
            "accepted_gap_count": len(gated.accepted_gaps),
            "observed_issue_gates": gates,
            "fallback_reason": gated.fallback_reason,
            "issues": [issue.model_dump() for issue in gated.issues],
            "accepted_claims": [
                claim.model_dump()
                for claim in gated.accepted_claims
            ],
            "accepted_gaps": [
                gap.model_dump()
                for gap in gated.accepted_gaps
            ],
        }

        if args.wave == "a":
            expected = WAVE_A_EXPECTED[case_id]
            record["preregistered_expected_disposition"] = expected
            record["disposition_match"] = gated.disposition == expected
            disposition_matches += int(gated.disposition == expected)

        if gated.accepted_claims:
            human_review.append(
                {
                    "case_id": case_id,
                    "question": row["question"],
                    "packet_id": packet.packet_id,
                    "claims": [
                        claim.model_dump()
                        for claim in gated.accepted_claims
                    ],
                }
            )
        results.append(record)

    report = {
        "schema_version": "dev-live-generation-eval-v1",
        "wave": args.wave,
        "bundle_manifest_sha256": manifest_hash,
        "prompt_sha256": prompt_hash,
        "source_commit": manifest["source_commit"],
        "provider": metadata.get("provider"),
        "model_id": metadata.get("model_id"),
        "parameters_or_effort": metadata.get(
            "parameters_or_effort"
        ),
        "case_count": len(cases),
        "evaluated_case_count": len(results),
        "callable_case_count": sum(
            row["generator_should_be_called"]
            for row in cases
        ),
        "issue_gate_counts": dict(sorted(issue_counts.items())),
        "fallback_reason_counts": dict(
            sorted(fallback_counts.items())
        ),
        "apparatus_errors": errors,
        "results": results,
        "human_review_queue": human_review,
        "non_claims": [
            "This is exploratory DEV-only evidence.",
            "No semantic-support rubric is frozen here.",
            "Accepted claims still require human review.",
            "TEST and PROSPECTIVE are not evaluated.",
        ],
    }
    if args.wave == "a":
        report["wave_a_disposition_matches"] = disposition_matches
        report["wave_a_disposition_total"] = len(WAVE_A_EXPECTED)

    report_path = out / f"wave-{args.wave}-gated-results.json"
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "disposition": (
                    "PASS_DEV_OUTPUT_REPLAY"
                    if not errors
                    else "FAIL_DEV_OUTPUT_REPLAY"
                ),
                "wave": args.wave,
                "bundle_manifest_sha256": manifest_hash,
                "case_count": len(cases),
                "evaluated_case_count": len(results),
                "issue_gate_counts": report["issue_gate_counts"],
                "fallback_reason_counts": report[
                    "fallback_reason_counts"
                ],
                "wave_a_disposition_matches": report.get(
                    "wave_a_disposition_matches"
                ),
                "wave_a_disposition_total": report.get(
                    "wave_a_disposition_total"
                ),
                "human_review_claim_cases": len(human_review),
                "apparatus_errors": errors,
                "report": str(report_path),
            },
            indent=2,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
