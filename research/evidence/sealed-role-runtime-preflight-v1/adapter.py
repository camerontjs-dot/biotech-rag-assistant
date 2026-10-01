"""Frozen no-model launcher for the named Codex sandbox permission profile.

Runs only deterministic probes. It cannot launch a research role or a model.
Runtime paths are supplied in a private binding, never inferred from answers.
"""

import hashlib
import json
import subprocess
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def profile(root, denied, permit=False):
    return {
        "filesystem": {
            ":root": "deny",
            ":minimal": "read",
            ":slash_tmp": "deny",
            ":tmpdir": "deny",
            str(root): "write",
            str(denied): "read" if permit else "deny",
        },
        "network": {"enabled": False},
    }


def toml_value(value):
    if isinstance(value, dict):
        return "{" + ",".join(
            json.dumps(k) + "=" + toml_value(v) for k, v in value.items()
        ) + "}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(value)


def command(binding, selected, argv):
    return [
        binding["cli"],
        "sandbox",
        "-C", binding["root"],
        "-P", "sealed_preflight_v1",
        "-c", "permissions.sealed_preflight_v1=" + toml_value(selected),
        "--",
        *argv,
    ]


def classify_read(returncode, stdout, stderr, expected_hash, denied=False, expected_bytes=None):
    if denied and expected_bytes and expected_bytes in stdout + stderr:
        return "FALSIFIED"
    if returncode == 0:
        if denied:
            return "FALSIFIED"
        return "PASS" if digest(stdout) == expected_hash else "APPARATUS_INVALID"
    if not denied:
        if b"Operation not permitted" in stderr or b"Permission denied" in stderr:
            return "FALSIFIED"
        return "APPARATUS_INVALID"
    if digest(stdout) == expected_hash or digest(stderr) == expected_hash:
        return "FALSIFIED"
    if b"Operation not permitted" in stderr or b"Permission denied" in stderr:
        return "PASS"
    return "INCONCLUSIVE"


def invoke(binding, selected, argv):
    """Physically run the installed CLI; timeout/crash is never a pass."""
    return subprocess.run(
        command(binding, selected, argv),
        cwd=binding["root"],
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin", "LANG": "C"},
        capture_output=True,
        timeout=30,
        check=False,
    )


def verify_fixture(binding, fixtures):
    root = Path(binding["root"]).resolve()
    denied = Path(binding["denied"]).resolve()
    allowed = Path(binding["allowed"]).resolve()
    if root in denied.parents or root not in allowed.parents:
        raise ValueError("incorrect fixture root")
    if (root / ".git").exists():
        raise ValueError("role root contains Git context")
    for key in ("allowed", "denied", "allowed_renamed", "denied_renamed"):
        if digest(Path(binding[key]).read_bytes()) != fixtures[key]["sha256"]:
            raise ValueError("fixture identity mismatch: " + key)
    if Path(binding["symlink"]).resolve() != denied:
        raise ValueError("symlink target mismatch")
