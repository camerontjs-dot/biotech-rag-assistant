"""Evaluate canonical citation-helper outcomes against the frozen contract probes.

The target-specific adapter is separate. It must emit one result per probe:
  {"id": "...", "status": "success", "text": "...", "start": 0, "end": 3}
  {"id": "...", "status": "refused", "reason": "..."}
  {"id": "...", "status": "error", "reason": "..."}

Unexpected errors are failures, not safe refusals. Offsets are half-open Unicode
codepoint positions, matching Python str slicing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SOURCE_SHA256 = "3666cec6252e3e3d074d49667cdc0f608c1bb8a5b907d39aa1db70de537fb101"


def evaluate(probe_path: Path, outcomes_path: Path) -> dict:
    raw = probe_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Frozen probe source changed: {digest}")
    probes = json.loads(raw)["cases"]
    outcomes = json.loads(outcomes_path.read_text())
    if isinstance(outcomes, dict):
        outcomes = outcomes["outcomes"]
    by_id = {}
    for outcome in outcomes:
        key = outcome["id"]
        if key in by_id:
            raise RuntimeError(f"Duplicate result: {key}")
        by_id[key] = outcome
    expected_ids = {p["id"] for p in probes}
    unexpected = sorted(set(by_id) - expected_ids)
    if unexpected:
        raise RuntimeError(f"Unexpected result IDs: {unexpected}")
    results = []
    for p in probes:
        o = by_id.get(p["id"], {"status": "missing"})
        failures = []
        status = o.get("status")
        policy = p["expected_outcome"]
        if status == "refused":
            if policy == "exact":
                failures.append("required ordinary sentence was refused")
        elif status == "success":
            if policy == "refuse":
                failures.append("successful span returned where refusal is required")
            text, start, end = o.get("text"), o.get("start"), o.get("end")
            if not isinstance(text, str):
                failures.append("span text is not a string")
            if type(start) is not int or type(end) is not int:
                failures.append("offsets are not integer codepoint positions")
            elif not 0 <= start <= end <= len(p["body"]):
                failures.append("offsets outside authorized body")
            elif p["body"][start:end] != text:
                failures.append("span text does not equal exact source slice")
            if isinstance(text, str) and p["quote"] not in text:
                failures.append("span does not contain the exact quote")
            if "expected_sentence" in p:
                expected = p["expected_sentence"]
                if text != expected["text"]:
                    failures.append("span omits sentence text or adds neighboring material")
                if (start, end) != (expected["start"], expected["end"]):
                    failures.append("offsets differ from the expected complete sentence")
        else:
            failures.append(f"unexpected outcome: {status}")
        results.append({"id":p["id"], "pass":not failures,
                        "expected_outcome":policy, "actual":o,
                        "failures":failures})
    return {"probe_sha256":digest, "total":len(results),
            "passed":sum(r["pass"] for r in results),
            "failed":sum(not r["pass"] for r in results),
            "results":results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("outcomes", type=Path)
    parser.add_argument("--probes", type=Path,
                        default=Path(__file__).with_name("preimplementation_probes.json"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = evaluate(args.probes, args.outcomes)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    raise SystemExit(bool(report["failed"]))
