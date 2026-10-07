#!/usr/bin/env python3
"""Local resource supervisor for one frozen semantic-author-slot-bound-v2 run.

Research infrastructure only. It never builds, alters, retries, repairs or interprets a
request or a response. For each named call it (1) waits for a free provider/memory/power
slot without signalling or inspecting any other process, (2) launches exactly the frozen
wrapper command once, (3) samples local resources while it runs, (4) preserves stdout,
stderr and the actual exit status, and (5) stops at the first failed, interrupted, invalid
or resource-stopped call. The wrapper still verifies the byte/hash freeze before each call.

Limits come from budget.json, which is published before any provider generation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

WRAPPER = "research/semantic_author_slot_boundary_v2.py"
AUTHOR_STATUS = "PASS_AUTHOR_PARTITION_STRUCTURE_ONLY"
CANARY_STATUS = "PASS_NONSEMANTIC_CANARY_ONLY"


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def run_text(argv, timeout=15):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    return result.stdout


def provider_ps(endpoint):
    with urllib.request.urlopen(endpoint + "/api/ps", timeout=5) as response:
        return json.loads(response.read())


def parse_free_percentage(text):
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", text)
    return int(match.group(1)) if match else None


def parse_swap_used_mib(text):
    match = re.search(r"used = ([\d.]+)([KMG])", text)
    if not match:
        return None
    scale = {"K": 1 / 1024, "M": 1.0, "G": 1024.0}[match.group(2)]
    return float(match.group(1)) * scale


def parse_battery(text):
    on_ac = "AC Power" in text
    match = re.search(r"(\d+)%", text)
    return (int(match.group(1)) if match else None), on_ac


def sample(budget):
    """One local observation. A probe that fails records None; it never raises."""
    out = {"at_utc": utc()}
    for key, probe in (
        ("free_percentage", lambda: parse_free_percentage(run_text(["memory_pressure"]))),
        ("pressure_level", lambda: int(run_text(["sysctl", "-n", "kern.memorystatus_vm_pressure_level"]).strip())),
        ("swap_used_mib", lambda: parse_swap_used_mib(run_text(["sysctl", "-n", "vm.swapusage"]))),
    ):
        try:
            out[key] = probe()
        except Exception as error:  # noqa: BLE001 - record, never hide
            out[key] = None
            out.setdefault("probe_errors", []).append(f"{key}: {type(error).__name__}")
    try:
        out["battery_percentage"], out["on_ac_power"] = parse_battery(run_text(["pmset", "-g", "batt"]))
    except Exception as error:  # noqa: BLE001
        out["battery_percentage"], out["on_ac_power"] = None, None
        out.setdefault("probe_errors", []).append(f"battery: {type(error).__name__}")
    try:
        out["thermal"] = " ".join(run_text(["pmset", "-g", "therm"]).split())[:200]
    except Exception:  # noqa: BLE001
        out["thermal"] = None
    try:
        models = provider_ps(budget["provider"]["endpoint"]).get("models", [])
        out["models"] = [{"name": m.get("name"), "digest": m.get("digest"), "size": m.get("size"),
                          "context_length": m.get("context_length")} for m in models]
    except Exception as error:  # noqa: BLE001
        out["models"] = None
        out.setdefault("probe_errors", []).append(f"provider_ps: {type(error).__name__}")
    return out


def start_blockers(snapshot, budget):
    need = budget["limits"]["start_requires"]
    reasons = []
    if snapshot["models"] is None:
        reasons.append("provider state unreadable")
    elif len(snapshot["models"]) != need["loaded_models"]:
        reasons.append("model resident: " + ",".join(str(m["name"]) for m in snapshot["models"]))
    if snapshot["free_percentage"] is None or snapshot["free_percentage"] < need["min_free_percentage"]:
        reasons.append(f"free_percentage {snapshot['free_percentage']} < {need['min_free_percentage']}")
    if snapshot["pressure_level"] != need["pressure_level"]:
        reasons.append(f"pressure_level {snapshot['pressure_level']} != {need['pressure_level']}")
    swap = snapshot["swap_used_mib"]
    if swap is None or swap >= need["max_swap_used_mib"]:
        reasons.append(f"swap_used_mib {swap} >= {need['max_swap_used_mib']}")
    battery = snapshot["battery_percentage"]
    if snapshot["on_ac_power"] is False and (battery is None or battery < need["min_battery_percentage_when_on_battery"]):
        reasons.append(f"battery {battery}% on battery power < {need['min_battery_percentage_when_on_battery']}")
    if snapshot["on_ac_power"] is None:
        reasons.append("power source unreadable")
    return reasons


class Watch:
    """Abort rules evaluated over the samples of one running call."""

    def __init__(self, budget, baseline):
        self.rule = budget["limits"]["abort_if"]
        self.baseline_swap = baseline["swap_used_mib"] or 0.0
        self.low_free = 0
        self.warn = 0
        self.failures = 0

    def check(self, snap):
        trips = []
        rule = self.rule
        free = snap["free_percentage"]
        if free is None or snap["pressure_level"] is None or snap["swap_used_mib"] is None:
            self.failures += 1
        else:
            self.failures = 0
        if self.failures >= rule["memory_probe_failures_consecutive"]:
            trips.append("memory probes failed repeatedly")
        self.low_free = self.low_free + 1 if free is not None and free < rule["free_percentage_below"] else 0
        if self.low_free >= rule["free_percentage_consecutive_samples"]:
            trips.append(f"free_percentage below {rule['free_percentage_below']}")
        level = snap["pressure_level"]
        if level is not None and level >= rule["pressure_level_at_least"]:
            trips.append(f"pressure_level {level}")
        self.warn = self.warn + 1 if level is not None and level >= 2 else 0
        if self.warn >= rule["pressure_level_warn_consecutive_samples"]:
            trips.append("pressure_level warn sustained")
        swap = snap["swap_used_mib"]
        if swap is not None and swap - self.baseline_swap >= rule["swap_growth_mib_at_least"]:
            trips.append(f"swap grew {swap - self.baseline_swap:.1f} MiB")
        for model in snap["models"] or []:
            if (model["size"] or 0) >= rule["resident_bytes_at_least"]:
                trips.append(f"resident {model['size']} bytes")
            if (model["context_length"] or 0) > rule["reported_context_above"]:
                trips.append(f"reported context {model['context_length']}")
        battery = snap["battery_percentage"]
        if snap["on_ac_power"] is False and battery is not None and battery < rule["battery_percentage_below_when_on_battery"]:
            trips.append(f"battery {battery}% on battery power")
        return trips


def log_event(log_dir, event):
    event = {"at_utc": utc(), **event}
    with (log_dir / "events.jsonl").open("a") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    print(json.dumps(event, sort_keys=True), flush=True)


def wait_for_slot(budget, log_dir, group):
    """Wait, without touching any other process, until the start limits hold."""
    limits = budget["limits"]
    began = time.monotonic()
    announced = None
    while True:
        snap = sample(budget)
        blockers = start_blockers(snap, budget)
        if not blockers:
            waited = time.monotonic() - began
            if announced:
                log_event(log_dir, {"event": "slot_free", "group": group, "waited_seconds": round(waited, 1)})
            return snap, round(waited, 1)
        waited = time.monotonic() - began
        if blockers != announced:
            log_event(log_dir, {"event": "waiting_for_slot", "group": group, "blockers": blockers,
                                "waited_seconds": round(waited, 1)})
            announced = blockers
        if waited >= limits["max_wait_for_slot_seconds"]:
            log_event(log_dir, {"event": "wait_exceeded_before_any_request", "group": group,
                                "blockers": blockers, "waited_seconds": round(waited, 1)})
            return None, round(waited, 1)
        time.sleep(limits["wait_poll_seconds_first_120s"] if waited < 120 else limits["wait_poll_seconds_after"])


LOG_PATTERNS = {
    "n_ctx": re.compile(r"llama_context: n_ctx\s+=\s+(\d+)"),
    "n_ctx_slot": re.compile(r"new slot, n_ctx = (\d+)"),
    "kv_buffer_mib": re.compile(r"KV buffer size =\s+([\d.]+) MiB"),
    "compute_buffer_mib": re.compile(r"compute buffer size =\s+([\d.]+) MiB"),
    "prompt_tokens_received": re.compile(r"new prompt, n_ctx_slot = (\d+), n_keep = (\d+), task\.n_tokens = (\d+)"),
    "prompt_eval": re.compile(r"\|\s+prompt eval time =\s+([\d.]+) ms /\s+(\d+) tokens"),
    "generation_eval": re.compile(r"\|\s+eval time =\s+([\d.]+) ms /\s+(\d+) tokens"),
    "slot_release": re.compile(r"stop processing: n_tokens = (\d+), truncated = (\d+)"),
    "generate_request": re.compile(r"\[GIN\].*\|\s+(\d+)\s+\|\s+([\w.µ]+)\s+\|.*POST\s+\"/api/generate\""),
}


def log_size(path):
    try:
        return path.stat().st_size
    except OSError:
        return None


def read_log_window(path, start, end):
    """Bytes the provider wrote during one call; None if unreadable or the log was rotated."""
    if start is None or end is None or end < start:
        return None
    try:
        with path.open("rb") as handle:
            handle.seek(start)
            return handle.read(end - start)
    except OSError:
        return None


def extract_log_facts(window):
    """Numbers only. The raw window stays private because it can include other clients."""
    if window is None:
        return {"status": "UNAVAILABLE"}
    text = window.decode("utf-8", "replace")
    found = {key: [m.groups() for m in pattern.finditer(text)] for key, pattern in LOG_PATTERNS.items()}
    releases = [{"n_tokens": int(a), "truncated": int(b)} for a, b in found["slot_release"]]
    return {"status": "OBSERVED" if releases else "NO_SLOT_RELEASE_IN_WINDOW",
            "window_bytes": len(window), "window_sha256": sha(window),
            "n_ctx": [int(g[0]) for g in found["n_ctx"]],
            "n_ctx_slot": [int(g[0]) for g in found["n_ctx_slot"]],
            "kv_buffer_mib": [float(g[0]) for g in found["kv_buffer_mib"]],
            "compute_buffer_mib": [float(g[0]) for g in found["compute_buffer_mib"]],
            "prompt_tokens_received": [int(g[2]) for g in found["prompt_tokens_received"]],
            "prompt_eval": [{"ms": float(a), "tokens": int(b)} for a, b in found["prompt_eval"]],
            "generation_eval": [{"ms": float(a), "tokens": int(b)} for a, b in found["generation_eval"]],
            "slot_releases": releases,
            "generate_requests": [{"http_status": int(a), "duration": b} for a, b in found["generate_request"]],
            "truncated_nonzero": sum(1 for r in releases if r["truncated"] != 0)}


def summarize(samples):
    free = [s["free_percentage"] for s in samples if s["free_percentage"] is not None]
    swap = [s["swap_used_mib"] for s in samples if s["swap_used_mib"] is not None]
    resident = [m["size"] for s in samples for m in (s["models"] or []) if m["size"]]
    contexts = [m["context_length"] for s in samples for m in (s["models"] or []) if m["context_length"]]
    foreign = sorted({m["name"] for s in samples for m in (s["models"] or [])})
    return {"samples": len(samples), "min_free_percentage": min(free) if free else None,
            "max_swap_used_mib": max(swap) if swap else None,
            "max_resident_bytes": max(resident) if resident else None,
            "max_reported_context": max(contexts) if contexts else None,
            "resident_model_names_seen": foreign,
            "min_battery_percentage": min([s["battery_percentage"] for s in samples
                                           if s["battery_percentage"] is not None], default=None),
            "thermal_values_seen": sorted({s["thermal"] for s in samples if s["thermal"]})}


def build_command(python, root, run, group):
    action = "canary" if group == "canary" else "run"
    command = [python, WRAPPER, action, "--root", str(root), "--run-dir", str(run)]
    if group != "canary":
        command += ["--group", group]
    return command


def stop_own_process(process):
    """Only the wrapper this supervisor started. Never any other process."""
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait()


def run_call(args, budget, group, log_dir):
    snap, waited = wait_for_slot(budget, log_dir, group)
    if snap is None:
        return {"outcome": "WAIT_EXCEEDED", "terminal": False, "group": group}
    command = build_command(args.python, args.root, args.run_dir, group)
    provider_log = Path(budget["context_evidence"]["provider_log"]).expanduser()
    log_start = log_size(provider_log)
    started = utc()
    began = time.monotonic()
    out_path, err_path = log_dir / f"{group}.stdout.txt", log_dir / f"{group}.stderr.txt"
    log_event(log_dir, {"event": "call_start", "group": group, "command": command, "start_sample": snap,
                        "provider_log_offset": log_start})
    samples, trips = [snap], []
    watch = Watch(budget, snap)
    with out_path.open("xb") as out, err_path.open("xb") as err:
        process = subprocess.Popen(command, cwd=args.root, stdout=out, stderr=err,
                                   start_new_session=True,
                                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        interval = budget["limits"]["sample_interval_seconds"]
        wall = budget["limits"]["per_call_wall_limit_seconds"]
        next_sample = time.monotonic() + interval
        try:
            while process.poll() is None:
                time.sleep(1)
                now = time.monotonic()
                if now >= next_sample:
                    next_sample = now + interval
                    observed = sample(budget)
                    samples.append(observed)
                    trips = watch.check(observed)
                    if trips:
                        log_event(log_dir, {"event": "abort_limit_tripped", "group": group, "trips": trips,
                                            "sample": observed})
                        stop_own_process(process)
                        break
                if now - began >= wall:
                    trips = [f"wall limit {wall}s"]
                    log_event(log_dir, {"event": "wall_limit", "group": group})
                    stop_own_process(process)
                    break
        except BaseException:
            # Never leave the wrapper running unsupervised: a second launch would overlap it.
            log_event(log_dir, {"event": "supervisor_interrupted", "group": group})
            stop_own_process(process)
            raise
        returncode = process.wait()
    finished = utc()
    final = sample(budget)
    samples.append(final)
    boundary_path = args.run_dir / "calls" / group / "author-boundary.json"
    status = None
    if boundary_path.is_file():
        try:
            status = json.loads(boundary_path.read_text())["status"]
        except Exception:  # noqa: BLE001
            status = "UNREADABLE"
    time.sleep(3)  # let the provider flush its log lines for this request
    log_end = log_size(provider_log)
    window = read_log_window(provider_log, log_start, log_end)
    if window is not None and args.private_dir is not None:
        args.private_dir.mkdir(parents=True, exist_ok=True)
        (args.private_dir / f"{group}.provider-log-window.private.txt").write_bytes(window)
    facts = extract_log_facts(window)
    expected = CANARY_STATUS if group == "canary" else AUTHOR_STATUS
    ok = (returncode == 0 and not trips and status == expected
          and facts.get("truncated_nonzero", 0) == 0)
    record = {"schema_version": "biotech-local-supervisor-call/v1", "group": group, "command": command,
              "started_utc": started, "finished_utc": finished,
              "wall_seconds": round(time.monotonic() - began, 1), "waited_for_slot_seconds": waited,
              "returncode": returncode, "stdout_sha256": sha(out_path.read_bytes()),
              "stderr_sha256": sha(err_path.read_bytes()), "boundary_status": status,
              "expected_status": expected, "resource_trips": trips, "resource": summarize(samples),
              "provider_log_window": {"start_offset": log_start, "end_offset": log_end, **facts},
              "end_sample": final, "accepted_by_supervisor": ok}
    (log_dir / f"{group}.supervisor.json").write_text(json.dumps(record, indent=1, sort_keys=True) + "\n")
    with (log_dir / f"{group}.samples.jsonl").open("w") as handle:
        for item in samples:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    log_event(log_dir, {"event": "call_end", "group": group, "returncode": returncode,
                        "boundary_status": status, "trips": trips, "accepted": ok,
                        "wall_seconds": record["wall_seconds"]})
    return {"outcome": "ACCEPTED" if ok else "FAILED", "terminal": not ok, "group": group,
            "returncode": returncode, "status": status, "trips": trips}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--budget", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--private-dir", type=Path, default=None,
                        help="outside the repository: raw provider-log windows that may hold other clients' lines")
    parser.add_argument("--dry-run", action="store_true", help="evaluate start limits only; start nothing")
    parser.add_argument("groups", nargs="*", help="canary and/or author-NN, in frozen order")
    args = parser.parse_args()
    args.root, args.run_dir = args.root.resolve(), args.run_dir.resolve()
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    budget = json.loads(args.budget.read_text())
    args.log_dir.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        snap = sample(budget)
        print(json.dumps({"sample": snap, "start_blockers": start_blockers(snap, budget)}, indent=1, sort_keys=True))
        return 0
    stop_marker = args.log_dir / "STOP.json"
    if stop_marker.exists():
        print("terminal stop recorded; this run's author sequence is closed", file=sys.stderr)
        return 3
    for group in args.groups:
        result = run_call(args, budget, group, args.log_dir)
        if result["outcome"] == "WAIT_EXCEEDED":
            return 4
        if result["terminal"]:
            stop_marker.write_text(json.dumps({"at_utc": utc(), **result}, sort_keys=True) + "\n")
            return 1
    log_event(args.log_dir, {"event": "sequence_complete", "groups": args.groups})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
