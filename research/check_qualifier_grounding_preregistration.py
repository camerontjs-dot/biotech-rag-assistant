"""Check frozen preparation contracts, not natural-language semantic support.

The ledgers contain declared semantic assessments. This checker verifies their
structure, authorized witness bindings, expectations and custody. A later pure
policy reducer may submit decisions to grade_submission; none is run by this CLI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "research/evidence/qualifier-grounding-policy-v1"
PREFIX = "research/evidence/qualifier-grounding-policy-v1/"
PREDECESSOR_PINS = {
    "research/evidence/wave-a-ep1-authority-readjudication-v1/adjudication.json":
        "6610b9a21ce7cc33cea39a197d4c689f8eacc6035be88caf6ecf6c502b8b6f21",
    "research/evidence/wave-a-ep1-authority-readjudication-v1/freeze.json":
        "ff7ba96166485e1af74a6896d9463bdbc83049f209d74eaf38e8577548403e61",
    "research/wave-a-ep1-authority-readjudication-protocol.md":
        "97120d8e6e1fc09036be92a096ec2c0c0d6ef99fd5cd35c345097147db3036b4",
    "research/evidence/wave-a-support-aperture-v1/evidence-manifest.json":
        "214aaf9723db10a3ccbcba43ecae0fede5cafa4f3ad5fc25bcbe598340bf8307",
    "DECISIONS.md": "8d2645c83864cf436d5312d8335843441c5dad8f84ca19e0002b317919383c95",
}
NORMATIVE_FILES = {
    PREFIX + name for name in (
        "policy.json", "interface.json", "inputs.jsonl", "expectations.jsonl", "pairs.json",
        "historical.json", "custody.json", "EXPERIMENT.json", "CANDIDATE.json",
    )
} | {
    "research/qualifier-grounding-policy-v1-protocol.md",
    "research/check_qualifier_grounding_preregistration.py",
    "tests/test_qualifier_grounding_preregistration.py",
}


class ContractError(ValueError):
    """An invalid preparation or submission, never a semantic verdict."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_bytes())


def read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_bytes().splitlines() if line.strip()]


def declared_support(ledger: dict, aperture: str) -> tuple[set, set, set]:
    """Aggregate explicit assessor inputs; perform no textual entailment inference."""
    supported, contradicted, ambiguous = set(), set(), set()
    allowed = {"QUOTE"} if aperture == "Q" else {"BODY"}
    for witness in ledger["witnesses"]:
        if witness["surface"] in allowed and aperture in witness["apertures"]:
            supported.update(witness["entails"])
            contradicted.update(witness["contradicts"])
            ambiguous.update(witness["ambiguous"])
    ambiguous.update(supported & contradicted)
    return supported, contradicted, ambiguous


def validate_ledger(ledger: dict, interface: dict) -> None:
    require(set(ledger) == set(interface["ledger_fields"]), "ledger fields")
    require(ledger["coverage"] in interface["coverage_values"], "coverage enum")
    require(ledger["integrity"] in interface["integrity_values"], "integrity enum")
    obligations = ledger["obligations"]
    require(bool(obligations), "missing material obligations")
    ids = [row["id"] for row in obligations]
    require(len(ids) == len(set(ids)), "duplicate obligation")
    for row in obligations:
        require(set(row) == set(interface["obligation_fields"]), "obligation fields")
        require(isinstance(row["id"], str) and bool(row["id"]), "obligation ID")
        require(row["materiality"] in interface["materiality_values"], "materiality enum")
    witnesses = ledger["witnesses"]
    witness_ids = [row["id"] for row in witnesses]
    require(len(witness_ids) == len(set(witness_ids)), "duplicate witness")
    for row in witnesses:
        require(set(row) == set(interface["witness_fields"]), "witness fields")
        require(isinstance(row["id"], str) and bool(row["id"]), "witness ID")
        require(row["surface"] in interface["witness_surface_values"], "witness surface")
        allowed = {"Q"} if row["surface"] == "QUOTE" else (
            {"N", "P"} if row["surface"] == "BODY" else set()
        )
        require(set(row["apertures"]) <= allowed, "unauthorized witness aperture")
        require("N" not in row["apertures"] or "P" in row["apertures"],
                "cited body outside packet")
        for field in ("entails", "contradicts", "ambiguous"):
            require(set(row[field]) <= set(ids), "witness references unknown obligation")
    proposal = ledger["proposal"]
    if proposal is not None:
        require(set(proposal) == set(interface["proposal_fields"]), "proposal fields")
        require(set(proposal["guards"]) == set(interface["guard_fields"]), "safety guards")
        require(all(value is None or isinstance(value, bool)
                    for value in proposal["guards"].values()), "guard must be bool or null")
        core, gaps = set(proposal["core_ids"]), set(proposal["gap_ids"])
        require(bool(core) and bool(gaps) and not core & gaps and core | gaps == set(ids),
                "core/gap must partition complete material obligations")
        require(set(proposal["body_witness_ids"]) <= set(witness_ids), "core witness missing")
        require(all(row["surface"] == "BODY" and "P" in row["apertures"]
                    for row in witnesses if row["id"] in proposal["body_witness_ids"]),
                "core witness not an admitted body")


def validate_decision(decision: dict, interface: dict, *, oracle: bool = False) -> None:
    fields = set(interface["output_fields"]) - ({"reason"} if oracle else set())
    require(set(decision) == fields, "decision fields; answer text is forbidden")
    require(isinstance(decision["case_id"], str), "case ID")
    for field in ("assessment_status", "grounding", "citation", "finding", "action"):
        require(decision[field] in interface[field + "_values"], f"{field} enum")
    require(set(decision["apertures"]) == {"Q", "N", "P"}, "aperture fields")
    require(all(value in interface["aperture_values"]
                for value in decision["apertures"].values()), "aperture enum")
    for field in ("core_ids", "gap_ids", "witness_ids"):
        require(isinstance(decision[field], list), f"{field} list")
        require(all(isinstance(value, str) for value in decision[field]), f"{field} ID")
        require(len(decision[field]) == len(set(decision[field])), f"{field} duplicates")
    if not oracle:
        require(isinstance(decision["reason"], str) and bool(decision["reason"].strip()),
                "missing decision rationale")


def validate_expectation(ledger: dict, decision: dict) -> None:
    """Reject internally inconsistent gold; do not author or assign semantic labels."""
    ids = {row["id"] for row in ledger["obligations"]}
    q, n, p = {ap: declared_support(ledger, ap) for ap in ("Q", "N", "P")}.values()
    if ledger["integrity"] != "VALID":
        require(decision["assessment_status"] == "APPARATUS_FAILURE" and
                decision["action"] == "STOP" and
                set(decision["apertures"].values()) == {"NOT_ASSESSED"},
                "apparatus failure must not masquerade as semantic judgment")
        return
    uncertain = (ledger["coverage"] == "UNKNOWN" or
                 any(row["materiality"] == "UNKNOWN" for row in ledger["obligations"]) or
                 any(support[2] for support in (q, n, p)) or
                 (ledger["proposal"] is not None and
                  any(value is None for value in ledger["proposal"]["guards"].values())))
    if uncertain:
        require(decision["assessment_status"] == "INCONCLUSIVE" and
                decision["action"] == "WITHHOLD" and not decision["core_ids"],
                "uncertainty must withhold the projection")
        return
    require(decision["assessment_status"] == "COMPLETE", "determinate control abstained")
    for aperture, support in zip(("Q", "N", "P"), (q, n, p), strict=True):
        declared_class = (
            "UNSUPPORTED" if support[1] or not support[0] else
            "SUPPORTED" if ids <= support[0] else "OVER_BROAD"
        )
        require(decision["apertures"][aperture] == declared_class,
                "declared aperture coverage disagrees with expectation")
    full_p = ids <= p[0] and not p[1]
    require((decision["grounding"] == "FULL_BODY_SUPPORT") == full_p,
            "body support and grounding expectation disagree")
    if full_p:
        require(set(decision["core_ids"]) == ids and not decision["gap_ids"],
                "supported condition discarded")
        if not (ids <= q[0] and ids <= n[0]):
            require(decision["finding"] == "CITATION_SPAN_INSUFFICIENCY" and
                    decision["action"] == "HOLD_FOR_CITATION", "citation/body conflation")
        else:
            require(decision["finding"] == "FULL_BODY_SUPPORT" and
                    decision["action"] == "KEEP_FULL", "fully supported control rejected")
    elif p[1]:
        require(decision["finding"] == "CONTRADICTED_CLAIM" and
                decision["action"] == "REJECT_COMPLETE", "contradiction hidden by trimming")
    elif not p[0]:
        require(decision["finding"] == "NO_SUPPORTED_CORE" and
                decision["action"] == "REJECT_COMPLETE", "core manufactured")
    else:
        proposal = ledger["proposal"]
        require(proposal is not None, "decomposition assessment absent")
        safe = all(proposal["guards"].values())
        if safe:
            require(decision["action"] == "PROPOSE_CORE_WITH_GAP" and
                    decision["finding"] == "UNSUPPORTED_MATERIAL_QUALIFIER" and
                    set(decision["core_ids"]) == set(proposal["core_ids"]) == p[0] and
                    set(decision["gap_ids"]) == set(proposal["gap_ids"]) == ids - p[0],
                    "unsafe, unsupported or incomplete core/gap expectation")
        else:
            require(decision["finding"] == "UNSAFE_DECOMPOSITION" and
                    decision["action"] == "REJECT_COMPLETE" and not decision["core_ids"],
                    "unsafe projection accepted")
    witness_lookup = {row["id"]: row for row in ledger["witnesses"]}
    require(set(decision["witness_ids"]) <= set(witness_lookup), "decision witness missing")
    supported_ids = set()
    for wid in decision["witness_ids"]:
        witness = witness_lookup[wid]
        require(witness["surface"] == "BODY" and "P" in witness["apertures"],
                "decision uses unauthorized support")
        supported_ids.update(witness["entails"])
    require(set(decision["core_ids"]) <= supported_ids, "core witness coverage absent")


def check_preregistration(package: Path = PACKAGE, root: Path = ROOT) -> dict:
    freeze = read_json(package / "freeze.json")
    require(set(freeze["files"]) == NORMATIVE_FILES, "freeze allowlist mismatch")
    for name, pin in freeze["files"].items():
        path = root / name
        require(not path.is_symlink() and digest(path) == pin["sha256"],
                f"preparation freeze drift: {name}")
    for name, pin in PREDECESSOR_PINS.items():
        require(digest(root / name) == pin, f"exact predecessor pin drift: {name}")
    custody = read_json(package / "custody.json")
    for name, pin in custody["verified_files_sha256"].items():
        path = root / name
        require(not path.is_symlink() and digest(path) == pin, f"predecessor drift: {name}")
    interface = read_json(package / "interface.json")
    inputs = read_rows(package / "inputs.jsonl")
    expectations = read_rows(package / "expectations.jsonl")
    ids = [row["case_id"] for row in inputs]
    require(len(ids) == len(set(ids)) == 28, "control count/duplicate drift")
    require(sorted(ids) == sorted(row["case_id"] for row in expectations),
            "expectation/input case mismatch")
    expected = {row["case_id"]: row for row in expectations}
    for row in inputs:
        require(set(row) == set(interface["input_fields"]), "candidate input leaks oracle fields")
        validate_ledger(row["ledger"], interface)
        verdict = expected[row["case_id"]]["expected"]
        require(verdict["case_id"] == row["case_id"], "gold case binding")
        validate_decision(verdict, interface, oracle=True)
        validate_expectation(row["ledger"], verdict)
    pairs = read_json(package / "pairs.json")["pairs"]
    require(len(pairs) == 9, "pair count drift")
    for pair in pairs:
        require(pair["from"] in expected and pair["to"] in expected, "pair case missing")
        if "INVARIANCE" in pair["kind"] or pair["kind"] == "BIJECTIVE_RENAMING":
            before = dict(expected[pair["from"]]["expected"])
            after = dict(expected[pair["to"]]["expected"])
            before.pop("case_id")
            after.pop("case_id")
            for key in ("core_ids", "gap_ids", "witness_ids"):
                before[key] = sorted(pair.get("rename", {}).get(v, v) for v in before[key])
                after[key] = sorted(after[key])
            require(before == after, "invariant expectation changed")
    historical = read_json(package / "historical.json")
    surfaces = read_json(root / historical["source_surfaces"])
    originals = {row["case_id"]: row for row in surfaces["observations"]}
    require(len(historical["observations"]) == 2, "historical anchor count")
    for row in historical["observations"]:
        original = originals[row["case_id"]]
        for key in ("exact_generated_claim", "exact_citation", "question", "packet_id",
                    "original_gates_fired", "original_public_disposition"):
            require(row[key] == original[key], f"historical drift: {row['case_id']}/{key}")
    return {
        "schema_version": "qualifier-grounding-preparation-check/v1",
        "status": "PASS_PREREGISTRATION_CONTRACT_ONLY",
        "controls": len(inputs), "pairs": len(pairs), "historical_anchors": 2,
        "custody_files": len(custody["verified_files_sha256"]),
        "freeze_sha256": digest(package / "freeze.json"),
        "checker_sha256": digest(Path(__file__)),
        "qualification": "NOT_RUN", "semantic_assessor": "NOT_IMPLEMENTED",
        "model_calls": 0, "generation_or_gate_replays": 0, "wave_b": "LOCKED",
    }


def grade_submission(submission: dict | None, expectations: list[dict], interface: dict) -> dict:
    """Mechanical future scoring interface; not called by the preparation CLI."""
    try:
        require(isinstance(submission, dict) and
                set(submission) == {"schema_version", "decisions"}, "missing/malformed submission")
        require(submission["schema_version"] == "qualifier-grounding-submission/v1",
                "submission version")
        decisions = submission["decisions"]
        require(isinstance(decisions, list), "submission decisions")
        expected = {row["case_id"]: row["expected"] for row in expectations}
        require(sorted(row["case_id"] for row in decisions) == sorted(expected),
                "missing/duplicate/extra candidate result")
        findings = []
        for row in decisions:
            validate_decision(row, interface)
            oracle = expected[row["case_id"]]
            differences = []
            for field, value in oracle.items():
                actual = row[field]
                if field in {"core_ids", "gap_ids", "witness_ids"}:
                    value, actual = sorted(value), sorted(actual)
                if value != actual:
                    differences.append(field)
            if differences:
                findings.append({"case_id": row["case_id"], "different_fields": differences,
                                 "candidate_action": row["action"],
                                 "unsafe_support": any(
                                     row["apertures"][ap] == "SUPPORTED" and
                                     oracle["apertures"][ap] != "SUPPORTED"
                                     for ap in ("Q", "N", "P")
                                 ) or bool(set(row["core_ids"]) - set(oracle["core_ids"]))})
        if not findings:
            outcome = "CONTRACT_MATCH_ONLY"
        elif all(row["candidate_action"] in {"WITHHOLD", "REJECT_COMPLETE"} and
                 not row["unsafe_support"] for row in findings):
            outcome = "MATERIALLY_WEAKENED"
        else:
            outcome = "FALSIFIED"
        return {"outcome": outcome, "findings": findings,
                "semantic_input_validity": "NOT_DETERMINED_BY_THIS_SCORER",
                "candidate_source_review": "REQUIRED_SEPARATELY"}
    except (ContractError, KeyError, TypeError, ValueError) as exc:
        return {"outcome": "APPARATUS_FAILURE", "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check_preregistration()
        code = 0
    except (OSError, KeyError, TypeError, ValueError) as exc:
        result = {"status": "APPARATUS_FAILURE", "error_type": type(exc).__name__,
                  "qualification": "NOT_RUN"}
        code = 2
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
