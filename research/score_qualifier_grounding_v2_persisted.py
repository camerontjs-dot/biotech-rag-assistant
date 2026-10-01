"""Score persisted fresh decisions; imports no candidate and invokes no reducer.

Profile: public-safe workbench verification, execution-owned, deterministic-source.
Authority: exact frozen expectations and pair definitions, never semantic truth.
Binds: v2 fresh persisted submissions. Tier: T1, failures explicitly reported.
Check: schema/canonical arrays, journal custody, exact fields, endpoint relations.
Escape: APPARATUS_INVALID for malformed/incomplete submissions; FALSIFIED for
valid contractual mismatches. No scoring result authorizes candidate repair.
"""

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def differences(actual, expected, path=""):
    if type(actual) is not type(expected):
        return [{"field": path, "actual": actual, "expected": expected}]
    if isinstance(expected, dict):
        result = []
        for key in sorted(actual.keys() | expected.keys()):
            if not path and key == "reason":
                continue
            child = path + "." + key if path else key
            if key not in actual or key not in expected:
                result.append({"field": child, "actual": actual.get(key),
                               "expected": expected.get(key), "missing_key": True})
            else:
                result.extend(differences(actual[key], expected[key], child))
        return result
    return [] if actual == expected else [{"field": path, "actual": actual, "expected": expected}]


def score(root, execution):
    spec = importlib.util.spec_from_file_location(
        "frozen_preparation_schema", root / "research/check_qualifier_grounding_v2_preparation.py"
    )
    prep = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prep)
    inputs = prep.lines(root, prep.FRESH / "inputs.jsonl")
    expected = {d["case_id"]: d for d in prep.lines(root, prep.FRESH / "expectations.jsonl")}
    interface = prep.load(root, prep.NORM / "interface.json")
    pairs = prep.load(root, prep.FRESH / "pairs.json")["pairs"]
    finish = prep.load(execution, "fresh-run-finish.json")
    submission = prep.load(execution, "fresh-submission.json")
    prep.require(set(submission) == {"schema_version", "decisions"} and
                 submission["schema_version"] == "qualifier-grounding-submission/v2",
                 "invalid submission format")
    decisions = submission["decisions"]
    prep.require(type(decisions) is list, "decisions must be an array")
    persisted = prep.lines(execution, "fresh-decisions.jsonl")
    prep.require(decisions == persisted, "submission differs from persisted decisions")
    prep.require(finish["execution_status"] == "COMPLETE" and finish["failure"] is None,
                 "incomplete decisive execution")
    prep.require(finish["decisions_sha256"] == digest(execution / "fresh-decisions.jsonl") and
                 finish["journal_sha256"] == digest(execution / "fresh-call-journal.jsonl"),
                 "decision/journal custody failure")
    prep.require(finish["input_sha256"] == digest(root / prep.FRESH / "inputs.jsonl"),
                 "input custody failure")
    prep.require(finish["calls_attempted"] == finish["calls_completed"] == len(inputs) == len(decisions),
                 "call/decision/input census differs")
    for decision in decisions:
        prep.require(not prep.schema_errors(interface["output_schema"], decision),
                     "malformed candidate decision")
        prep.canonical_arrays(decision)
    actual = {d["case_id"]: d for d in decisions}
    prep.require(len(actual) == len(decisions) and set(actual) == set(expected),
                 "missing/duplicate/extra decision")
    journal = prep.lines(execution, "fresh-call-journal.jsonl")
    prep.require(len(journal) == 2 * len(inputs), "incomplete call journal")
    counts = {}
    for index, case in enumerate(inputs):
        start, saved = journal[2 * index:2 * index + 2]
        prep.require(start["event"] == "CALL_STARTED" and saved["event"] == "DECISION_PERSISTED",
                     "invalid journal sequence")
        prep.require(start["index"] == saved["index"] == index and
                     start["case_id"] == saved["case_id"] == case["case_id"], "journal input identity")
        encoded = json.dumps(decisions[index], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        prep.require(saved["decision_sha256"] == hashlib.sha256(encoded.encode()).hexdigest(),
                     "journal decision identity")
        counts[case["case_id"]] = counts.get(case["case_id"], 0) + 1
    prep.require(all(value == 1 for value in counts.values()), "repeated reducer call")
    case_results = []
    exact = {}
    for case in inputs:
        identifier = case["case_id"]
        mismatch = differences(actual[identifier], expected[identifier])
        exact[identifier] = not mismatch
        case_results.append({"case_id": identifier, "schema_valid": True,
                             "exact_except_reason": exact[identifier], "mismatches": mismatch})
    pair_results = []
    for pair in pairs:
        lhs, rhs = actual[pair["left"]], actual[pair["right"]]
        fields, error = [], None
        try:
            if pair["relation"] == "RENAMED_INVARIANT":
                lhs = prep.renamed(lhs, pair["renaming"])
            for field in pair["compare_fields"]:
                equal = prep.get_field(lhs, field) == prep.get_field(rhs, field)
                fields.append({"field": field, "requirement": "EQUAL", "passed": equal})
            for field in pair["must_change"]:
                changed = prep.get_field(lhs, field) != prep.get_field(rhs, field)
                fields.append({"field": field, "requirement": "DIFFERENT", "passed": changed})
        except (KeyError, prep.PreparationError) as exc:
            error = {"type": type(exc).__name__, "message": str(exc)}
        relation_pass = error is None and all(field["passed"] for field in fields)
        endpoints_exact = exact[pair["left"]] and exact[pair["right"]]
        pair_results.append({"pair_id": pair["pair_id"], "relation": pair["relation"],
                             "left": pair["left"], "right": pair["right"],
                             "relation_pass": relation_pass, "left_exact": exact[pair["left"]],
                             "right_exact": exact[pair["right"]], "both_endpoints_exact": endpoints_exact,
                             "strict_pair_pass": relation_pass and endpoints_exact,
                             "field_results": fields, "relation_error": error})
    passing = all(exact.values()) and all(pair["strict_pair_pass"] for pair in pair_results)
    result = {
        "schema_version": "qualifier-grounding-fresh-scoring/v2",
        "scored_at_utc": datetime.now(timezone.utc).isoformat(), "apparatus_status": "VALID",
        "candidate_commit": finish["candidate_commit"], "candidate_tree": finish["candidate_tree"],
        "fresh_set_id": prep.load(root, prep.FRESH / "freeze.json")["set_id"],
        "decision_count": len(decisions), "exact_decisions": sum(exact.values()),
        "mismatched_decisions": len(exact) - sum(exact.values()),
        "pair_count": len(pairs), "relation_passes": sum(p["relation_pass"] for p in pair_results),
        "strict_pair_passes": sum(p["strict_pair_pass"] for p in pair_results),
        "schema_failures": 0, "reducer_calls_during_scoring": 0,
        "decisions_persisted_before_scoring": True, "call_counts": counts,
        "case_results": case_results, "pair_results": pair_results,
        "control_disposition": "PASS_STRICT_FRESH_GATES" if passing else "FALSIFIED",
        "source_oracle_review_required_separately": True,
        "expectation_limits": "Frozen agent-authored symbolic hypotheses, needs-audit; no semantic-assessor truth.",
    }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--execution", required=True, type=Path)
    args = parser.parse_args()
    result = score(args.root, args.execution)
    (args.execution / "fresh-scoring.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    summary = {key: value for key, value in result.items()
               if key not in ("case_results", "pair_results", "call_counts")}
    print(json.dumps(summary, indent=2))
    return 0 if result["control_disposition"] == "PASS_STRICT_FRESH_GATES" else 1


if __name__ == "__main__":
    raise SystemExit(main())
