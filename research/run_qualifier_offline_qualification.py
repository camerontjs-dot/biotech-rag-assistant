"""Run one frozen ledger candidate once, then score persisted decision-only output.

Post-reveal qualification apparatus; never imported by the frozen reducer.
Profile: deterministic-operation; public-safe; evidence owner is the experiment.
The exclusive run marker prevents rerunning this experiment in the same checkout.
"""

import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "research/evidence/qualifier-grounding-offline-qualification-v1"
PACKAGE = ROOT / "research/evidence/qualifier-grounding-policy-v1"
SOURCE = "research/qualifier_grounding_reducer.py"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def normalized(decision, rename=None):
    rename = rename or {}
    value = {k: v for k, v in decision.items() if k not in {"case_id", "reason"}}
    for key in ("core_ids", "gap_ids", "witness_ids"):
        value[key] = sorted(rename.get(x, x) for x in value[key])
    return value


def score_pairs(decisions, cases):
    lookup = {x["case_id"]: x for x in decisions}
    pair_results = []
    for pair in json.loads((PACKAGE / "pairs.json").read_bytes())["pairs"]:
        before, after = lookup[pair["from"]], lookup[pair["to"]]
        kind = pair["kind"]
        if "INVARIANCE" in kind or kind == "BIJECTIVE_RENAMING":
            checks = {
                "same_decision_modulo_opaque_ids_and_rationale": (
                    normalized(before, pair.get("rename")) == normalized(after)
                )
            }
        elif kind == "BODY_SUPPORT_ADDITION":
            checks = {
                "packet_defect_to_body_support": (
                    before["grounding"] == "PACKET_LEVEL_GROUNDING_DEFECT"
                    and after["grounding"] == "FULL_BODY_SUPPORT"
                ),
                "packet_aperture_becomes_supported": (
                    before["apertures"]["P"] != "SUPPORTED"
                    and after["apertures"]["P"] == "SUPPORTED"
                ),
                "quote_omission_remains": (
                    before["apertures"]["Q"] == after["apertures"]["Q"] != "SUPPORTED"
                    and after["action"] == "HOLD_FOR_CITATION"
                ),
                "known_gap_resolved": bool(before["gap_ids"]) and not after["gap_ids"],
            }
        elif kind == "BODY_SUPPORT_REMOVAL":
            checks = {
                "body_support_to_packet_defect": (
                    before["grounding"] == "FULL_BODY_SUPPORT"
                    and after["grounding"] == "PACKET_LEVEL_GROUNDING_DEFECT"
                ),
                "packet_support_removed": (
                    before["apertures"]["P"] == "SUPPORTED"
                    and after["apertures"]["P"] != "SUPPORTED"
                ),
                "safe_core_and_explicit_gap": (
                    after["action"] == "PROPOSE_CORE_WITH_GAP"
                    and bool(after["core_ids"])
                    and bool(after["gap_ids"])
                ),
            }
        elif kind == "QUOTE_WIDENING":
            checks = {
                "quote_insufficiency_resolved": (
                    before["apertures"]["Q"] != "SUPPORTED"
                    and after["apertures"]["Q"] == "SUPPORTED"
                    and before["citation"] != "SUFFICIENT"
                    and after["citation"] == "SUFFICIENT"
                ),
                "body_apertures_unchanged": all(
                    before["apertures"][a] == after["apertures"][a] for a in ("N", "P")
                ),
                "packet_support_and_retained_ids_unchanged": all(
                    before[k] == after[k] for k in ("grounding", "core_ids", "gap_ids")
                ),
            }
        elif kind == "DEPENDENCY_SENSITIVITY":
            checks = {
                "safe_core_to_unsafe_rejection": (
                    before["action"] == "PROPOSE_CORE_WITH_GAP"
                    and after["action"] == "REJECT_COMPLETE"
                    and after["finding"] == "UNSAFE_DECOMPOSITION"
                    and not after["core_ids"]
                ),
                "support_assessments_unchanged": before["apertures"] == after["apertures"],
            }
        else:
            raise ValueError("Unrecognized frozen pair relation")
        relation_pass = all(checks.values())
        endpoints = cases[pair["from"]]["match"] and cases[pair["to"]]["match"]
        pair_results.append(
            {
                **pair,
                "checks": checks,
                "relation_pass": relation_pass,
                "endpoints_match_contract": endpoints,
                "strict_pair_pass": relation_pass and endpoints,
            }
        )
    return pair_results


def main():
    candidate = json.loads((OUTPUT / "CANDIDATE.json").read_bytes())
    input_bytes = (PACKAGE / "inputs.jsonl").read_bytes()
    assert sha(input_bytes) == "8667dd6fa1718f16c9a0ba445380f15c9c31befffee18a72b2c1f843d132228f"
    source = subprocess.check_output(
        ["git", "-C", str(ROOT), "show", candidate["source_commit"] + ":" + SOURCE]
    )
    assert sha(source) == candidate["implementation_files"][SOURCE]
    assert (ROOT / SOURCE).read_bytes() == source
    inputs = [json.loads(line) for line in input_bytes.splitlines() if line.strip()]
    assert len(inputs) == len({row["case_id"] for row in inputs}) == 28
    namespace = {}
    exec(compile(source, SOURCE, "exec"), namespace)
    run = {
        "schema_version": "qualifier-grounding-decisive-run/v1",
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate_commit": candidate["source_commit"],
        "candidate_tree": candidate["source_tree"],
        "source_sha256": sha(source),
        "input_sha256": sha(input_bytes),
        "runner_sha256": sha(Path(__file__).read_bytes()),
        "planned_decide_calls": 28,
        "decide_calls": 0,
        "runtime_forbidden_accesses": [],
        "project_model_provider_calls": 0,
        "generation_or_gate_replays": 0,
        "wave_b": "LOCKED",
        "expectations_exposed_to_reducer": False,
        "source_load": "exact Git object; source extraction occurs outside reducer execution",
    }
    with (OUTPUT / "run-started.json").open("x") as marker:
        json.dump(run, marker, indent=2)
        marker.write("\n")
    executing = False

    def audit(event, args):
        if executing and (
            event == "open"
            or event.startswith(("socket.", "subprocess.", "ctypes."))
            or event in {"os.system", "os.putenv", "os.unsetenv", "os.chdir"}
        ):
            run["runtime_forbidden_accesses"].append({"event": event})
            raise RuntimeError("Forbidden reducer runtime access")

    def trace(frame, event, arg):
        if frame.f_code.co_filename == SOURCE and event == "call":
            if frame.f_code.co_name == "decide":
                run["decide_calls"] += 1
        return trace

    sys.addaudithook(audit)
    decisions = []
    try:
        sys.settrace(trace)
        for row in inputs:
            executing = True
            try:
                decisions.append(namespace["decide"](row))
            finally:
                executing = False
    except Exception as exc:
        run.update(status="APPARATUS_FAILURE", error_type=type(exc).__name__, error=str(exc))
        write("decisive-run.json", run)
        return 2
    finally:
        sys.settrace(None)
    submission = {"schema_version": "qualifier-grounding-submission/v1", "decisions": decisions}
    write("decisions.json", submission)
    (OUTPUT / "decisions.jsonl").write_text(
        "".join(json.dumps(x, sort_keys=True) + "\n" for x in decisions)
    )
    run.update(
        status="EXECUTED",
        completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        decision_count=len(decisions),
        decision_sha256=sha((OUTPUT / "decisions.json").read_bytes()),
    )
    write("decisive-run.json", run)

    # Scoring starts only after candidate decisions have been persisted and hashed.
    expectations = [
        json.loads(line) for line in (PACKAGE / "expectations.jsonl").read_bytes().splitlines()
    ]
    interface = json.loads((PACKAGE / "interface.json").read_bytes())
    spec = importlib.util.spec_from_file_location(
        "frozen_scorer", ROOT / "research/check_qualifier_grounding_preregistration.py"
    )
    scorer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scorer)
    scored = scorer.grade_submission(submission, expectations, interface)
    write("frozen-scorer.json", scored)
    expected = {x["case_id"]: x["expected"] for x in expectations}
    cases = {}
    for actual in decisions:
        oracle = expected[actual["case_id"]]
        differences = {
            k: {"expected": v, "actual": actual[k]}
            for k, v in oracle.items()
            if (sorted(v) if isinstance(v, list) else v)
            != (sorted(actual[k]) if isinstance(actual[k], list) else actual[k])
        }
        cases[actual["case_id"]] = {
            "match": not differences,
            "differences": differences,
            "action": actual["action"],
            "finding": actual["finding"],
        }
    write("case-results.json", cases)
    pairs = score_pairs(decisions, cases)
    write(
        "pair-results.json",
        {
            "pair_count": len(pairs),
            "results": pairs,
            "relation_passes": sum(x["relation_pass"] for x in pairs),
            "strict_pair_passes": sum(x["strict_pair_pass"] for x in pairs),
            "strict_definition": "relation holds AND both endpoint controls match",
        },
    )
    print(
        json.dumps(
            {
                "candidate_decide_calls": run["decide_calls"],
                "controls": len(cases),
                "exact_matches": sum(x["match"] for x in cases.values()),
                "frozen_scorer_outcome": scored["outcome"],
                "pair_relations_hold": sum(x["relation_pass"] for x in pairs),
                "strict_pair_passes": sum(x["strict_pair_pass"] for x in pairs),
            }
        )
    )
    return 0 if scored["outcome"] == "CONTRACT_MATCH_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
