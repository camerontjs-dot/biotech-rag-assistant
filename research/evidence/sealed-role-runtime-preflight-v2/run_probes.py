"""One decisive no-model preflight; preserve each raw stream before scoring."""

import argparse
import datetime
import json
import subprocess
from pathlib import Path

from adapter import (
    classify_read,
    command,
    digest,
    environment,
    invoke,
    observe_configuration,
    verify_custody,
)


def now():
    return datetime.datetime.now(datetime.UTC).isoformat()


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def public_value(value, binding):
    """Private bytes remain unchanged; redact local paths in the public copy."""
    if isinstance(value, str):
        for actual, logical in sorted(
            binding["public_path_map"].items(), key=lambda item: -len(item[0])
        ):
            value = value.replace(actual, logical)
        return value
    if isinstance(value, list):
        return [public_value(item, binding) for item in value]
    if isinstance(value, dict):
        return {public_value(key, binding): public_value(item, binding)
                for key, item in value.items()}
    return value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--binding", required=True, type=Path)
    args = parser.parse_args()
    binding = json.loads(args.binding.read_text())
    custody = args.binding.parent
    evidence = Path(__file__).parent
    checkout = evidence.parents[2]
    candidate = json.loads((evidence / "CANDIDATE.json").read_text())
    freeze = json.loads((custody / "candidate-freeze.json").read_text())
    fixtures = json.loads((evidence / "fixtures.json").read_text())
    with (custody / "DECISIVE_RUN_STARTED").open("x") as stream:
        stream.write(now() + "\n")
    records = []
    counts = {"sandbox_invocations": 0, "configuration_observations": 0,
              "model_inference_requests": 0, "research_role_launches": 0,
              "assessor_calls": 0, "reducer_calls": 0, "project_generation_calls": 0}
    disposition = "APPARATUS_INVALID"
    started = now()
    probes = evidence / "probes"
    probes.mkdir()

    def observe(tag, kind):
        counts["configuration_observations"] += 1
        receipt = observe_configuration(binding, custody, tag, kind)
        expected = candidate["effective_stable_sha256"][kind]
        status = "PASS" if receipt["stable_sha256"] == expected else "APPARATUS_INVALID"
        record = {"probe": tag, "kind": kind, "timestamp": now(), "status": status,
                  "observed": receipt, "expected_stable_sha256": expected}
        save(probes / (tag + ".json"), public_value(record, binding))
        records.append({"probe": tag, "status": status})
        return status

    def run(tag, argv, fixture=None, denied=False, kind="baseline"):
        counts["sandbox_invocations"] += 1
        invocation = {"probe": tag, "candidate_id": candidate[
            "candidate_id" if kind == "baseline" else "mutation_candidate_id"
        ], "started_at_utc": now(), "argv": command(binding, argv, kind),
            "cwd": binding["role_root"], "environment": environment(binding, kind)}
        save(custody / (tag + ".invocation.json"), invocation)
        result = invoke(binding, argv, kind)
        (custody / (tag + ".stdout")).write_bytes(result.stdout)
        (custody / (tag + ".stderr")).write_bytes(result.stderr)
        raw = {**invocation, "finished_at_utc": now(), "exit_code": result.returncode,
               "stdout_sha256": digest(result.stdout), "stderr_sha256": digest(result.stderr),
               "stdout": result.stdout.decode(errors="replace"),
               "stderr": result.stderr.decode(errors="replace")}
        save(custody / (tag + ".raw.json"), raw)
        if fixture:
            expected = Path(binding[fixture]).read_bytes()
            status = classify_read(result, expected, denied)
        else:
            lines = result.stdout.decode(errors="replace").splitlines()
            if result.returncode != 0:
                status = "APPARATUS_INVALID"
            elif not lines or lines[0] != binding["role_root"]:
                status = "FALSIFIED"
            elif "CODEX_SANDBOX=seatbelt" not in lines[1:]:
                status = "INCONCLUSIVE"
            else:
                status = "PASS"
        public = public_value({**raw, "status": status, "fixture": fixture,
                               "denied": denied}, binding)
        public["public_stdout_sha256"] = digest(public["stdout"].encode())
        public["public_stderr_sha256"] = digest(public["stderr"].encode())
        save(probes / (tag + ".json"), public)
        records.append({"probe": tag, "status": status})
        return status

    try:
        if subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
        ).strip() != freeze["candidate_commit"]:
            raise ValueError("execution checkout is not the frozen candidate commit")
        dirty = subprocess.check_output(
            ["git", "-C", str(checkout), "status", "--porcelain"], text=True
        ).strip()
        if dirty:
            raise ValueError("checkout is not clean before P0")
        for name, expected in freeze["source_sha256"].items():
            if digest((evidence / name).read_bytes()) != expected:
                raise ValueError("source drift: " + name)
        verify_custody(binding, fixtures)
        schedule = [
            ("P0", lambda: observe("P0", "baseline")),
            ("P1", lambda: run("P1", ["/bin/sh", "-c", "pwd -P; /usr/bin/env"])),
            ("P2", lambda: run("P2", ["/bin/cat", binding["allowed"]], "allowed")),
            ("P3", lambda: run("P3", ["/bin/cat", binding["denied"]], "denied", True)),
            ("P4-parent", lambda: run("P4-parent", [
                "/bin/cat", "../sibling/" + Path(binding["denied"]).name,
            ], "denied", True)),
            ("P4-sibling", lambda: run("P4-sibling", [
                "/bin/cat", "../sibling/./" + Path(binding["denied"]).name,
            ], "denied", True)),
            ("P4-symlink", lambda: run("P4-symlink", [
                "/bin/cat", binding["symlink"],
            ], "denied", True)),
            ("P4-tmp-alias", lambda: run("P4-tmp-alias", [
                "/bin/cat", binding["denied"].replace("/private/tmp/", "/tmp/", 1),
            ], "denied", True)),
            ("P5-state", lambda: observe("P5-state", "mutation")),
            ("P5", lambda: run("P5", [
                "/bin/cat", binding["denied"],
            ], "denied", False, "mutation")),
            ("P6-allowed", lambda: run("P6-allowed", [
                "/bin/cat", binding["allowed_renamed"],
            ], "allowed_renamed")),
            ("P6-denied", lambda: run("P6-denied", [
                "/bin/cat", binding["denied_renamed"],
            ], "denied_renamed", True)),
        ]
        for _, action in schedule:
            disposition = action()
            if disposition != "PASS":
                break
        else:
            disposition = "SUPPORTED_FOR_SEALED_ROLE_PREFLIGHT"
        verify_custody(binding, fixtures)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
        save(evidence / "execution-error.json", public_value({
            "timestamp": now(), "error_type": type(error).__name__, "error": str(error),
            "after_records": records,
        }, binding))
        disposition = "APPARATUS_INVALID"
    finally:
        receipt = {"schema_version": "sealed-runtime-probe-run/v2", "started_at_utc": started,
                   "finished_at_utc": now(), "candidate_commit": freeze["candidate_commit"],
                   "candidate_tree": freeze["candidate_tree"], "records": records,
                   "counts": counts, "terminal_disposition": disposition,
                   "stop_policy": "first non-PASS; no repair, retry or later probe"}
        save(evidence / "probe-run.json", receipt)
        print(json.dumps(receipt, indent=2))
    return 0 if disposition == "SUPPORTED_FOR_SEALED_ROLE_PREFLIGHT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
