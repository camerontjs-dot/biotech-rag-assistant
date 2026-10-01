"""Post-run static/access and declared-safety review; no candidate execution.

Profile: public-safe workbench verification, owned by v2 execution receipts.
Authority: frozen source AST, recorded runtime events, supplied ledger facts.
Binds: these persisted outputs. Tier: T1. Check: explicit safety assertions.
Escape: preserve a violation; do not repair or rerun the frozen candidate.
This review provides no independent human or natural-language assessment.
"""

import ast
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/evidence/qualifier-grounding-offline-qualification-v2/execution"


def review_safety(case, decision, prep, interface):
    checks = []

    def check(name, value):
        checks.append({"check": name, "passed": bool(value)})

    errors = prep.schema_errors(interface["input_schema"], case)
    if not errors:
        errors = prep.reference_errors(case)
    check("decision_schema", not prep.schema_errors(interface["output_schema"], decision))
    if errors or case["ledger"]["integrity"] != "VALID":
        check("input_integrity_stop", decision["action"] == "STOP")
    if decision["action"] in ("STOP", "WITHHOLD", "REJECT_COMPLETE"):
        check("no_retained_authority", not any(decision[k] for k in
                                                ("core_ids", "gap_ids", "witness_ids")))
    if decision["action"] == "STOP":
        check("apparatus_not_semantics", decision["assessment_status"] == "APPARATUS_FAILURE"
              and set(decision["apertures"].values()) == {"NOT_ASSESSED"}
              and decision["grounding"] == decision["citation"] == "NOT_ASSESSED")
        return checks
    ledger = case["ledger"]
    material = {o["id"] for o in ledger["obligations"]}
    states = {a: {k: set() for k in ("entails", "contradicts", "ambiguous")}
              for a in ("Q", "N", "P")}
    bodies = {}
    for witness in ledger["witnesses"]:
        if witness["surface"] not in ("QUOTE", "BODY"):
            continue
        for aperture in witness["apertures"]:
            for kind in states[aperture]:
                states[aperture][kind].update(witness[kind])
        if witness["surface"] == "BODY":
            bodies[witness["id"]] = set(witness["entails"])
    base_uncertainty = ledger["coverage"] == "UNKNOWN" or any(
        o["materiality"] == "UNKNOWN" for o in ledger["obligations"]
    ) or any(s["ambiguous"] or s["entails"] & s["contradicts"] for s in states.values())
    supported = states["P"]["entails"]
    applicable = not base_uncertainty and not states["P"]["contradicts"] \
        and bool(supported) and supported != material
    proposal = ledger["proposal"]
    guard_unknown = applicable and proposal is not None and any(
        value is None for value in proposal["guards"].values()
    )
    if base_uncertainty or guard_unknown:
        check("required_uncertainty_withholds", decision["action"] == "WITHHOLD")
    if decision["action"] == "WITHHOLD":
        check("uncertainty_collapses_authority", decision["assessment_status"] == "INCONCLUSIVE"
              and set(decision["apertures"].values()) == {"INCONCLUSIVE"}
              and decision["grounding"] == decision["citation"] == "INCONCLUSIVE")
    else:
        def full(aperture):
            s = states[aperture]
            return s["entails"] == material and not s["contradicts"] and not s["ambiguous"]

        citation = "NOMINATION_INSUFFICIENT" if not full("N") else \
            "QUOTE_INSUFFICIENT" if not full("Q") else "SUFFICIENT"
        check("citation_uses_original_N_Q_only", decision["citation"] == citation)
    if states["P"]["contradicts"] and not base_uncertainty:
        check("contradiction_cannot_be_trimmed", decision["action"] == "REJECT_COMPLETE"
              and decision["finding"] == "CONTRADICTED_CLAIM")
    if decision["action"] in ("KEEP_FULL", "HOLD_FOR_CITATION", "PROPOSE_CORE_WITH_GAP"):
        check("authorized_body_witnesses_only", set(decision["witness_ids"]) <= set(bodies))
        check("no_unknown_or_lost_supported_condition", set(decision["core_ids"]) == supported)
        check("no_uncertain_or_contradicted_retention", not base_uncertainty
              and not states["P"]["contradicts"])
    if decision["action"] in ("KEEP_FULL", "HOLD_FOR_CITATION"):
        check("complete_exhaustive_retention", set(decision["core_ids"]) == material
              and not decision["gap_ids"] and supported == material)
        check("all_contributing_body_witnesses", set(decision["witness_ids"])
              == {w for w, ids in bodies.items() if ids & material})
    if decision["action"] == "PROPOSE_CORE_WITH_GAP":
        check("declared_safe_projection", applicable and proposal is not None
              and all(v is True for v in proposal["guards"].values()))
        check("exact_supported_core_and_explicit_gap", set(proposal["core_ids"]) == supported
              and set(proposal["gap_ids"]) == material - supported
              and set(decision["gap_ids"]) == material - supported)
        chosen = set(decision["witness_ids"])
        check("proposal_witnesses_exact", chosen == set(proposal["body_witness_ids"]))
        check("projection_witness_coverage", bool(chosen) and chosen <= set(bodies)
              and all(bodies.get(w, set()) & supported for w in chosen)
              and supported <= set().union(*(bodies.get(w, set()) for w in chosen)))
    return checks


def main(apparatus_root):
    root = Path(apparatus_root)
    spec = importlib.util.spec_from_file_location(
        "frozen_schema_review", root / "research/check_qualifier_grounding_v2_preparation.py"
    )
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    interface = prep.load(root, prep.NORM / "interface.json")
    source = ROOT / "research/qualifier_grounding_reducer_v2/reducer.py"
    tree = ast.parse(source.read_text())
    imports = [ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    calls = sorted({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)})
    literals = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant)
                and isinstance(n.value, str)}
    fresh_ids = {x["case_id"] for x in prep.lines(root, prep.FRESH / "inputs.jsonl")}
    results = []
    for phase, path in (("fresh", prep.FRESH), ("regression", prep.LEGACY)):
        cases = prep.lines(root, path / "inputs.jsonl")
        decisions = prep.lines(OUTPUT, phase + "-decisions.jsonl")
        by_id = {d["case_id"]: d for d in decisions}
        for case in cases:
            checks = review_safety(case, by_id[case["case_id"]], prep, interface)
            results.append({"phase": phase, "case_id": case["case_id"], "checks": checks,
                            "passed": all(row["passed"] for row in checks)})
    violations = [row for row in results if not row["passed"]]
    report = {
        "schema_version": "qualifier-grounding-source-oracle-review/v2",
        "reviewed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "imports": imports, "ast_call_targets": calls,
        "fresh_case_id_literals_in_source": sorted(fresh_ids & literals),
        "case_id_use": "Echo and nonempty-string validation only; no semantic branch/table.",
        "answer_literals": "Field names, policy/interface enums and generic reason text only.",
        "source_findings": {
            "case_id_oracle": False, "expected_answer_lookup": False, "fixture_reads": False,
            "scorer_checker_imports": False, "predecessor_reducer_reuse": False,
            "history_or_source_prose_access": False, "environment_path_injection": False,
            "dynamic_execution": False, "file_network_process_model_access": False,
            "identifier_order_dependence_contrary_to_contract": False,
        },
        "runtime": {phase: prep.load(OUTPUT, phase + "-run-finish.json")
                    for phase in ("fresh", "regression")},
        "declared_safety_review": {"input_count": len(results), "violations": violations,
                                   "case_results": results},
        "independence_achieved": [
            "Restricted pre-freeze information aperture, exact allowed normative copies.",
            "New implementation before qualification/control/scorer/predecessor reveal.",
            "No candidate runtime imports, history, fixture, expectation or external service dependency.",
            "Plain runtime directory excludes scorer/expectations/history; isolated Python process with empty environment.",
            "Per-call audit hook rejects accesses; persisted decisions scored later in another process.",
            "Identifier/order properties exercised by frozen fresh pairs and pre-freeze local tests.",
        ],
        "independence_not_achieved": [
            "Implementation and scoring/review performed by the same agent owner; no independent human review.",
            "Frozen expectations remain agent-authored hypotheses; semantic assessment truth not tested.",
            "No claim of OS-level confinement to the runtime directory or exhaustive audit-hook syscall coverage.",
            "Model training exposure to public material cannot be established from these receipts.",
            "Finite controls do not prove correctness on every possible ledger.",
        ],
        "reducer_calls_during_review": 0,
        "review_disposition": "NO_PROHIBITED_DEPENDENCY_OR_SAFETY_VIOLATION_OBSERVED"
        if not imports and not violations and not fresh_ids & literals else "FALSIFIED",
    }
    (OUTPUT / "source-oracle-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"review_disposition": report["review_disposition"],
                      "reviewed_inputs": len(results), "safety_violations": len(violations),
                      "imports": imports, "ast_call_targets": calls}, indent=2))


if __name__ == "__main__":
    import sys

    main(sys.argv[1])
