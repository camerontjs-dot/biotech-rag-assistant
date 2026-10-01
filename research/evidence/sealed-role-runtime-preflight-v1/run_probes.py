"""Run the frozen deterministic preflight once and persist each child result.

No model request, project engine, provider, network probe, or research role.
Private binding and raw streams stay outside the public repository.
"""

import argparse
import datetime
import json
import os
import subprocess
from pathlib import Path

import adapter


def now():
    return datetime.datetime.now(datetime.UTC).isoformat()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as output:
        output.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--freeze-commit", required=True)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    binding = json.loads(args.binding.read_text())
    custody = args.binding.parent
    fixtures = json.loads((evidence / "fixtures.json").read_text())
    candidate = json.loads((evidence / "CANDIDATE.json").read_text())
    policy = adapter.profile(binding["root"], binding["denied"])
    if adapter.digest(Path(binding["cli"]).read_bytes()) != binding["cli_sha256"]:
        raise ValueError("runtime binary drift")
    adapter.verify_fixture(binding, fixtures)
    for name, expected in candidate["source_sha256"].items():
        if adapter.digest((evidence / name).read_bytes()) != expected:
            raise ValueError("frozen source drift: " + name)
    if adapter.digest(adapter.toml_value(policy).encode()) != candidate["exact_policy_sha256"]:
        raise ValueError("policy drift")
    checkout = evidence.parents[2]
    head = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
    ).strip()
    dirty = subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain"], text=True
    ).strip()
    if head != args.freeze_commit or dirty:
        raise ValueError("candidate freeze or checkout custody failed")
    results = []

    def safe(text):
        substitutions = sorted(binding["public_path_map"].items(), key=lambda p: -len(p[0]))
        for original, replacement in substitutions:
            text = text.replace(original, replacement)
        return text

    def run(probe_id, argv, selected=policy, key=None, denied=False):
        started = now()
        cmd = adapter.command(binding, selected, argv)
        write(custody / (probe_id + ".invocation.json"), {
            "command": cmd, "cwd": binding["root"],
            "environment": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C"},
        })
        failure = None
        try:
            result = adapter.invoke(binding, selected, argv)
        except subprocess.TimeoutExpired as error:
            failure = "TIMEOUT"
            result = subprocess.CompletedProcess(cmd, 124, error.stdout or b"", error.stderr or b"")
        except OSError as error:
            failure = type(error).__name__
            result = subprocess.CompletedProcess(cmd, 127, b"", str(error).encode())
        (custody / (probe_id + ".stdout")).write_bytes(result.stdout)
        (custody / (probe_id + ".stderr")).write_bytes(result.stderr)
        if failure:
            verdict = "APPARATUS_INVALID"
            expected = None
        elif key:
            expected = fixtures[key]["sha256"]
            verdict = adapter.classify_read(
                result.returncode, result.stdout, result.stderr, expected,
                denied=denied, expected_bytes=Path(binding[key]).read_bytes(),
            )
        else:
            actual = result.stdout.decode(errors="replace").splitlines()
            correct_root = result.returncode == 0 and actual and actual[0] == binding["root"]
            verdict = "PASS" if correct_root else "APPARATUS_INVALID"
            expected = None
        receipt = {
            "schema_version": "sealed-runtime-preflight-probe/v1",
            "probe_id": probe_id, "started_at_utc": started, "ended_at_utc": now(),
            "candidate_id": candidate["candidate_id"], "freeze_commit": args.freeze_commit,
            "policy_sha256": adapter.digest(adapter.toml_value(selected).encode()),
            "command": [safe(x) for x in cmd], "cwd": "fixture/role",
            "exit_code": result.returncode,
            "stdout": safe(result.stdout.decode(errors="replace")),
            "stderr": safe(result.stderr.decode(errors="replace")),
            "raw_stdout_sha256": adapter.digest(result.stdout),
            "raw_stderr_sha256": adapter.digest(result.stderr),
            "expected_sha256": expected,
            "expected_access": "READ_DENIED" if denied else "READ_SUCCEEDS" if key else (
                "START_IN_ROLE_ROOT"
            ),
            "observed_access": "READ_SUCCEEDED" if key and result.returncode == 0 else (
                "READ_FAILED" if key else verdict
            ),
            "verdict": verdict, "model_calls": 0, "research_role_calls": 0,
            "execution_failure": failure,
            "private_invocation_sha256": adapter.digest(
                (custody / (probe_id + ".invocation.json")).read_bytes()
            ),
        }
        write(evidence / "probes" / (probe_id + ".json"), receipt)
        results.append(receipt)
        return verdict

    stop = run("P7", ["/bin/sh", "-c", "pwd -P; /usr/bin/env"])
    if stop == "PASS":
        stop = run("P1", ["/bin/cat", binding["allowed"]], key="allowed")
    if stop == "PASS":
        stop = run("P2", ["/bin/cat", binding["denied"]], key="denied", denied=True)
    if stop == "PASS":
        for name, path in (
            ("traversal", os.path.relpath(binding["denied"], binding["root"])),
            ("sibling", binding["sibling_route"]),
            ("symlink", binding["symlink"]),
            ("tmp_alias", binding["tmp_alias"]),
        ):
            stop = run("P3_" + name, ["/bin/cat", path], key="denied", denied=True)
            if stop != "PASS":
                break
    if stop == "PASS":
        selected = adapter.profile(binding["root"], binding["denied"], permit=True)
        stop = run("P4_control", ["/bin/cat", binding["denied"]], selected, key="denied")
    if stop == "PASS":
        selected = adapter.profile(binding["root"], binding["denied_renamed"])
        stop = run("P5_allowed", ["/bin/cat", binding["allowed_renamed"]], selected,
                   key="allowed_renamed")
        if stop == "PASS":
            stop = run("P5_denied", ["/bin/cat", binding["denied_renamed"]], selected,
                       key="denied_renamed", denied=True)
    if stop == "PASS":
        stop = "INCONCLUSIVE"
    write(evidence / "probe-run.json", {
        "started_at_utc": results[0]["started_at_utc"], "ended_at_utc": now(),
        "candidate_id": candidate["candidate_id"], "freeze_commit": args.freeze_commit,
        "probe_count": len(results), "completed_probes": [r["probe_id"] for r in results],
        "stop_disposition": stop, "no_model_or_role_request": True,
        "initialization_limit": "No model initialization audit; cannot accept sealed-role claim.",
        "model_calls": 0, "research_role_calls": 0,
    })
    print(json.dumps({"disposition": stop, "probes": len(results), "model_calls": 0}))
    return 1 if stop == "FALSIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
