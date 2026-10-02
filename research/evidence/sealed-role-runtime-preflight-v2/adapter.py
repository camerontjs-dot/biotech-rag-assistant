"""No-model runtime launcher and configuration observer.

All policy enforcement belongs to the installed Codex sandbox. The observer
reads configuration diagnostics; it does not intercept or deny child reads.
Exact local paths and original streams stay in the private custody binding.
"""

import hashlib
import json
import os
import selectors
import subprocess
import time
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def environment(binding, kind="baseline"):
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "LANG": "C",
        "CODEX_HOME": binding["config_homes"][kind],
    }


def command(binding, argv, kind="baseline"):
    return [
        binding["cli"], "sandbox", "-C", binding["role_root"],
        "-P", "sealed_preflight_v2", "--", *argv,
    ]


def invoke(binding, argv, kind="baseline"):
    return subprocess.run(
        command(binding, argv, kind), cwd=binding["role_root"],
        env=environment(binding, kind), capture_output=True, timeout=30, check=False,
    )


def rpc_configuration(binding, custody, tag, kind="baseline"):
    """Only initialize and read diagnostics. No thread, turn or command RPC."""
    requests = [
        {"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "sealed_runtime_preflight", "version": "2"},
            "capabilities": {"experimentalApi": True},
        }},
        {"method": "initialized"},
        {"id": 2, "method": "config/read", "params": {
            "cwd": binding["role_root"], "includeLayers": True,
        }},
        {"id": 3, "method": "configRequirements/read", "params": {}},
        {"id": 4, "method": "permissionProfile/list", "params": {
            "cwd": binding["role_root"],
        }},
    ]
    argv = [binding["cli"], "app-server", "--stdio"]
    trace = (custody / (tag + ".rpc.jsonl")).open("x")
    error_stream = (custody / (tag + ".rpc.stderr")).open("xb")
    process = subprocess.Popen(
        argv, cwd=binding["role_root"], env=environment(binding, kind),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=error_stream,
    )
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    pending = bytearray()
    responses = {}
    try:
        for request in requests:
            trace.write(json.dumps({"direction": "request", "message": request}) + "\n")
            trace.flush()
            process.stdin.write(encoded(request) + b"\n")
            process.stdin.flush()
            if "id" not in request:
                continue
            deadline = time.monotonic() + 20
            while request["id"] not in responses:
                if time.monotonic() > deadline:
                    raise TimeoutError("configuration RPC did not complete")
                if b"\n" not in pending:
                    if not selector.select(timeout=1):
                        if process.poll() is not None:
                            raise RuntimeError("configuration runtime exited")
                        continue
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        raise RuntimeError("configuration response missing")
                    pending.extend(chunk)
                while b"\n" in pending:
                    line, _, tail = pending.partition(b"\n")
                    pending = bytearray(tail)
                    trace.write(json.dumps({"direction": "response", "raw": line.decode()})
                                + "\n")
                    trace.flush()
                    response = json.loads(line)
                    if "id" in response:
                        if "error" in response:
                            raise RuntimeError("configuration RPC error: " + str(response))
                        responses[response["id"]] = response["result"]
        return responses
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait(timeout=5)
        selector.close()
        trace.close()
        error_stream.close()


def observe_configuration(binding, custody, tag, kind="baseline"):
    """Persist actual loaded layers and runtime-resolved summary before scoring."""
    responses = rpc_configuration(binding, custody, tag, kind)
    diagnostic = subprocess.run(
        [binding["cli"], "doctor", "--json"], cwd=binding["role_root"],
        env=environment(binding, kind), capture_output=True, timeout=30, check=False,
    )
    (custody / (tag + ".doctor.stdout")).write_bytes(diagnostic.stdout)
    (custody / (tag + ".doctor.stderr")).write_bytes(diagnostic.stderr)
    doctor = json.loads(diagnostic.stdout)
    load = doctor["checks"]["config.load"]
    sandbox = doctor["checks"]["sandbox.helpers"]
    if load["status"] != "ok" or sandbox["status"] != "ok":
        raise RuntimeError("runtime did not expose resolved configuration")
    config = responses[2]["config"]
    if config.get("sandbox_mode") is not None or config.get("sandbox_workspace_write"):
        raise ValueError("unexpected inherited legacy sandbox configuration")
    if config.get("default_permissions") != "sealed_preflight_v2":
        raise ValueError("unexpected active default permission profile")
    profiles = responses[4]
    if profiles.get("nextCursor") or not any(
        row["id"] == "sealed_preflight_v2" and row["allowed"] for row in profiles["data"]
    ):
        raise ValueError("profile is missing, forbidden or incompletely enumerated")
    if load["details"]["cwd"] != binding["role_root"]:
        raise ValueError("configuration cwd differs")
    if load["details"]["CODEX_HOME"] != binding["config_homes"][kind]:
        raise ValueError("configuration home differs")
    resolved = {key: sandbox["details"][key] for key in (
        "filesystem sandbox", "network sandbox", "denied-read rules",
        "denied-read glob rules", "managed filesystem source", "glob scan max depth",
    )}
    if resolved["filesystem sandbox"] != "restricted":
        raise ValueError("resolved filesystem is not restricted")
    stable = {
        "loaded": {key: config.get(key) for key in (
            "default_permissions", "sandbox_mode", "sandbox_workspace_write", "permissions",
            "shell_environment_policy", "allow_login_shell", "analytics",
        )},
        "layers": responses[2]["layers"], "origins": responses[2]["origins"],
        "requirements": responses[3], "profiles": profiles, "resolved": resolved,
    }
    receipt = {
        "stable": stable, "stable_sha256": digest(encoded(stable)),
        "doctor_exit_code": diagnostic.returncode,
        "doctor_stdout_sha256": digest(diagnostic.stdout),
        "doctor_stderr_sha256": digest(diagnostic.stderr),
        "rpc_trace_sha256": digest((custody / (tag + ".rpc.jsonl")).read_bytes()),
        "rpc_stderr_sha256": digest((custody / (tag + ".rpc.stderr")).read_bytes()),
        "doctor_overall_status": doctor["overallStatus"],
        "limitation": "Resolved diagnostic summary; no compiled Seatbelt/kernel rule dump.",
    }
    (custody / (tag + ".effective.json")).write_bytes(encoded(receipt) + b"\n")
    return receipt


def classify_read(result, expected, denied=False):
    """Positive-control bytes are exact. Successful or partial denied reads veto."""
    if denied:
        if result.returncode == 0 or result.stdout:
            return "FALSIFIED"
        if any(expected[index:index + 8] in result.stderr for index in range(len(expected) - 7)):
            return "FALSIFIED"
        if b"sandbox_apply" in result.stderr or b"No such file" in result.stderr:
            return "APPARATUS_INVALID"
        if result.stderr.startswith(b"cat:") and (
            b"Operation not permitted" in result.stderr or b"Permission denied" in result.stderr
        ):
            return "PASS"
        return "INCONCLUSIVE"
    if result.returncode == 0:
        return "PASS" if result.stdout == expected else "APPARATUS_INVALID"
    if result.stderr.startswith(b"cat:") and (
        b"Operation not permitted" in result.stderr or b"Permission denied" in result.stderr
    ):
        return "FALSIFIED"
    return "APPARATUS_INVALID"


def verify_custody(binding, fixtures):
    if digest(Path(binding["cli"]).read_bytes()) != binding["cli_sha256"]:
        raise ValueError("runtime binary drift")
    root = Path(binding["role_root"])
    if (root / ".git").exists() or (root / ".codex").exists():
        raise ValueError("role root contains repository/config context")
    for key in ("allowed", "denied", "allowed_renamed", "denied_renamed"):
        path = Path(binding[key])
        if digest(path.read_bytes()) != fixtures[key]["sha256"]:
            raise ValueError("fixture drift: " + key)
        if (root in path.parents) != key.startswith("allowed"):
            raise ValueError("fixture root class mismatch")
    if Path(binding["symlink"]).resolve() != Path(binding["denied"]):
        raise ValueError("symlink identity drift")
    for kind, expected in binding["configuration_sha256"].items():
        if digest((Path(binding["config_homes"][kind]) / "config.toml").read_bytes()) != expected:
            raise ValueError("configuration bytes drift")
