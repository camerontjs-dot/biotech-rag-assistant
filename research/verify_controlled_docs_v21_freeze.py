#!/usr/bin/env python3
"""Verify the frozen controlled-docs-v2.1 repository object."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    args = parser.parse_args()
    root = args.benchmark.resolve()

    sums_path = root / "SHA256SUMS"
    freeze_path = root / "freeze_receipt.json"
    manifest_path = root / "corpus_manifest.json"

    errors: list[str] = []
    expected: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        if path in expected:
            errors.append(f"duplicate checksum entry: {path}")
        expected[path] = digest

    files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS"
    )
    observed_paths = {str(path.relative_to(root)) for path in files}
    if observed_paths != set(expected):
        errors.append(
            "SHA256SUMS path set differs from benchmark files: "
            f"missing={sorted(observed_paths - set(expected))}, "
            f"extra={sorted(set(expected) - observed_paths)}"
        )

    mismatches = []
    for rel, digest in sorted(expected.items()):
        path = root / rel
        if path.exists():
            observed = sha256(path)
            if observed != digest:
                mismatches.append(
                    {"path": rel, "expected": digest, "observed": observed}
                )
    if mismatches:
        errors.append(f"checksum mismatches: {mismatches}")

    tree_files = sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.name not in {"SHA256SUMS", "freeze_receipt.json"}
    )
    listing = "".join(
        f"{sha256(path)}  {path.relative_to(root)}\n"
        for path in tree_files
    )
    tree_hash = hashlib.sha256(listing.encode()).hexdigest()

    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if tree_hash != freeze.get("tree_sha256"):
        errors.append(
            f"tree hash mismatch: observed {tree_hash}, "
            f"receipt {freeze.get('tree_sha256')}"
        )
    if freeze.get("file_count") != len(files) + 1:
        errors.append(
            f"file_count mismatch: receipt {freeze.get('file_count')}, "
            f"observed including SHA256SUMS {len(files) + 1}"
        )
    if freeze.get("benchmark") != "controlled-docs-v2.1":
        errors.append("freeze benchmark identity is not controlled-docs-v2.1")
    if manifest.get("status") != "frozen_candidate_for_slice2":
        errors.append("manifest status is not frozen_candidate_for_slice2")

    prospective = manifest.get("prospective", {})
    if freeze.get("prospective_sha256") != prospective.get(
        "commitment_sha256"
    ):
        errors.append("manifest/freeze prospective commitment mismatch")
    if freeze.get("prospective_file_sha256") != prospective.get(
        "file_sha256"
    ):
        errors.append("manifest/freeze prospective file hashes mismatch")

    report = {
        "disposition": (
            "PASS_FROZEN_V21_IDENTITY"
            if not errors
            else "FAIL_FROZEN_V21_IDENTITY"
        ),
        "benchmark": freeze.get("benchmark"),
        "file_count": len(files) + 1,
        "checksum_entries": len(expected),
        "tree_sha256": tree_hash,
        "freeze_receipt_sha256": sha256(freeze_path),
        "prospective_sha256": freeze.get("prospective_sha256"),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
