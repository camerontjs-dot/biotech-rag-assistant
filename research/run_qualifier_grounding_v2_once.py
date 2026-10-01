"""Exclusive offline execution harness; never derives or scores a decision.

Profile: workbench deterministic operation, public-safe, execution-owned.
Authority: physical call journal and persisted decisions, not semantic truth.
Frozen preparation and candidate source are immutable. This harness is copied
into a plain runtime directory with reducer.py, inputs.jsonl and settings.json.
Binds: this candidate/phase. Tier: T2 for repeated execution in that directory.
Check: exclusive start receipt, per-call fsync journal, source/input hashes.
Escape: preserve partial files and stop APPARATUS_INVALID without a retry.
"""

import hashlib
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def stamp():
    return datetime.now(timezone.utc).isoformat()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_record(stream, record):
    stream.write(encode(record) + "\n")
    stream.flush()
    os.fsync(stream.fileno())


def unique_keys(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON object key")
        result[key] = value
    return result


def main():
    root = Path(__file__).resolve().parent
    settings = json.loads((root / "settings.json").read_text(), object_pairs_hook=unique_keys)
    source = (root / "reducer.py").read_bytes()
    inputs = (root / "inputs.jsonl").read_bytes()
    assert hashlib.sha256(source).hexdigest() == settings["candidate_source_sha256"]
    assert hashlib.sha256(inputs).hexdigest() == settings["input_sha256"]
    lines = inputs.decode().splitlines()
    assert all(line.strip() for line in lines)
    cases = [json.loads(line, object_pairs_hook=unique_keys) for line in lines]
    ids = [case["case_id"] for case in cases]
    assert len(cases) == settings["required_input_count"] == len(set(ids))
    active = False
    access_events = []

    def audit(event, arguments):
        if active:
            access_events.append({"event": event,
                                  "argument_types": [type(x).__name__ for x in arguments]})
            raise RuntimeError("Prohibited runtime access during reducer call: " + event)

    sys.addaudithook(audit)
    spec = importlib.util.spec_from_file_location("frozen_candidate", root / "reducer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    decide = module.decide
    with (root / "run-start.json").open("x") as stream:
        write_record(stream, {**settings, "started_at_utc": stamp(),
                              "run_exclusivity": "O_EXCL via open mode x",
                              "input_ids": ids,
                              "visible_runtime_files": sorted(p.name for p in root.iterdir()),
                              "expectations_scorer_or_history_present": False})
    attempted = completed = 0
    failure = None
    with (root / "call-journal.jsonl").open("x") as journal, \
            (root / "decisions.jsonl").open("x") as decisions:
        try:
            for index, case in enumerate(cases):
                before = encode(case)
                attempted += 1
                write_record(journal, {"event": "CALL_STARTED", "index": index,
                                       "case_id": ids[index], "at_utc": stamp(),
                                       "input_line_sha256": hashlib.sha256(lines[index].encode()).hexdigest()})
                active = True
                try:
                    decision = decide(case)
                finally:
                    active = False
                assert encode(case) == before, "Reducer mutated its input"
                write_record(decisions, decision)
                completed += 1
                write_record(journal, {"event": "DECISION_PERSISTED", "index": index,
                                       "case_id": ids[index], "at_utc": stamp(),
                                       "decision_sha256": hashlib.sha256(encode(decision).encode()).hexdigest()})
        except (Exception, KeyboardInterrupt, SystemExit) as exc:  # noqa: BLE001 - preserve partial execution
            failure = {"type": type(exc).__name__, "message": str(exc)}
    receipt = {**settings, "finished_at_utc": stamp(), "calls_attempted": attempted,
               "calls_completed": completed, "calls_per_input": 1,
               "execution_status": "COMPLETE" if failure is None else "APPARATUS_INVALID",
               "runtime_audit_events": access_events, "input_mutation_observed": False,
               "failure": failure,
               "decisions_sha256": hashlib.sha256((root / "decisions.jsonl").read_bytes()).hexdigest(),
               "journal_sha256": hashlib.sha256((root / "call-journal.jsonl").read_bytes()).hexdigest()}
    with (root / "run-finish.json").open("x") as stream:
        write_record(stream, receipt)
    print(encode(receipt))
    return 0 if failure is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
