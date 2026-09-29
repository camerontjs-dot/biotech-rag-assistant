#!/usr/bin/env python3
"""Acceptance checks for the controlled-docs-v2.1 B04 numeric-collision repair."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import coverage

NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?")
MIN_REPAIR_CASES = 8
MIN_PER_SPLIT = 4
MIN_PROCESS_AREAS_PER_SPLIT = 3


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_equal_tree(left: Path, right: Path, label: str, errors: list[str]) -> None:
    def files(root: Path) -> dict[str, bytes]:
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    a, b = files(left), files(right)
    if a.keys() != b.keys():
        errors.append(f"{label}: file sets differ")
        return
    changed = [name for name in a if a[name] != b[name]]
    if changed:
        errors.append(f"{label}: bytes differ: {changed[:8]}")


def doc_lookup(corpus_dir: Path) -> tuple[dict[tuple[str, str], object], dict[str, str]]:
    corpus = load_corpus(corpus_dir)
    by_key = {}
    by_id_area = {}
    for document in corpus.documents:
        key = (document.metadata.doc_id, document.metadata.version)
        by_key[key] = document
    return by_key, by_id_area


def numeric_tokens(text: str) -> set[str]:
    return set(NUMBER_RE.findall(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v2", type=Path, required=True)
    parser.add_argument("--v21", type=Path, required=True)
    args = parser.parse_args()
    v2, v21 = args.v2.resolve(), args.v21.resolve()
    errors: list[str] = []
    observations: list[str] = []

    # Repair scope: corpus and adversarial bytes stay identical to the frozen predecessor.
    check_equal_tree(v2 / "corpus", v21 / "corpus", "corpus", errors)
    check_equal_tree(v2 / "adversarial", v21 / "adversarial", "adversarial", errors)

    if (v21 / "freeze_receipt.json").exists():
        errors.append("freeze_receipt.json must not exist while v2.1 is under construction")
    if (v21 / "SHA256SUMS").exists():
        errors.append("SHA256SUMS must not exist while v2.1 is under construction")

    manifest = json.loads((v21 / "corpus_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("benchmark") != "controlled-docs-v2.1":
        errors.append("manifest benchmark must be controlled-docs-v2.1")
    if manifest.get("status") != "construction":
        errors.append("manifest status must remain construction before freeze")
    predecessor = manifest.get("predecessor", {})
    if predecessor.get("commit") != "379a3e65942e8af7dcf21a4d24077642d45b364d":
        errors.append("manifest predecessor commit drifted")
    if predecessor.get("tree_sha256") != (
        "bbf8410cf9da9c82bc04b31a731241b197d9827b58f31842de5496a12b364670"
    ):
        errors.append("manifest predecessor tree receipt drifted")

    cases = []
    for split, filename in (("DEV", "dev_cases.jsonl"), ("TEST", "test_cases.jsonl")):
        for row in jsonl(v21 / "cases" / filename):
            if row["split"] != split:
                errors.append(f"{row.get('case_id')}: split/file mismatch")
            cases.append(row)
    by_case = {row["case_id"]: row for row in cases}
    if len(by_case) != len(cases):
        errors.append("duplicate case_id in runtime cases")

    families = json.loads((v21 / "evaluator_only/families.json").read_text(encoding="utf-8"))
    gold = []
    for filename in ("dev_relevance.jsonl", "test_relevance.jsonl"):
        gold.extend(jsonl(v21 / "evaluator_only/gold" / filename))
    gold_by_case: dict[str, list[dict]] = defaultdict(list)
    for row in gold:
        gold_by_case[row["case_id"]].append(row)

    # Document/process-area authority from the manifest.
    process_area = {
        (row["doc_id"], str(row["version"])): row["process_area"]
        for row in manifest["documents"]
    }
    corpus = load_corpus(v21 / "corpus")
    docs = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }

    repair_ids = sorted(
        cid for cid, info in families.items()
        if "numeric_collision" in info.get("tags", [])
        and "post_failure_repair" in info.get("tags", [])
    )
    if len(repair_ids) < MIN_REPAIR_CASES:
        errors.append(
            f"need at least {MIN_REPAIR_CASES} numeric-collision repair cases; found {len(repair_ids)}"
        )

    split_counts = Counter(by_case[cid]["split"] for cid in repair_ids if cid in by_case)
    for split in ("DEV", "TEST"):
        if split_counts[split] < MIN_PER_SPLIT:
            errors.append(
                f"need at least {MIN_PER_SPLIT} {split} repair cases; found {split_counts[split]}"
            )

    split_areas: dict[str, set[str]] = defaultdict(set)
    overlap_rows = {}
    seen_questions = Counter(row["question"].strip().lower() for row in cases)

    for cid in repair_ids:
        case = by_case.get(cid)
        family = families.get(cid)
        spans = gold_by_case.get(cid, [])
        if case is None:
            errors.append(f"{cid}: repair family entry has no runtime case")
            continue
        if family.get("family") != "B04":
            errors.append(f"{cid}: repair case primary family must be B04")
        area = family.get("process_area")
        split_areas[case["split"]].add(area)
        if seen_questions[case["question"].strip().lower()] != 1:
            errors.append(f"{cid}: question duplicates another runtime question")

        dispositions = {row["expected_disposition"] for row in spans}
        if dispositions != {"answer"}:
            errors.append(f"{cid}: repair case must have answer disposition, got {sorted(dispositions)}")
        decisive = [row for row in spans if row["decisive"]]
        hard = [row for row in spans if row["relevance_class"] == "hard_negative"]
        if len(decisive) != 1:
            errors.append(f"{cid}: expected exactly one decisive span; found {len(decisive)}")
            continue
        if len(hard) < 3:
            errors.append(f"{cid}: expected >=3 hard-negative spans; found {len(hard)}")

        target = decisive[0]
        target_key = (target["doc_id"], str(target["version"]))
        target_doc = docs.get(target_key)
        if target_doc is None or not target_doc.is_retrievable:
            errors.append(f"{cid}: decisive span is not in a retrievable document")
            continue
        if process_area.get(target_key) != area:
            errors.append(f"{cid}: family process_area does not match decisive document")

        target_text = target_doc.raw_text[target["char_start"]:target["char_end"]]
        if target_text != target["span_text"]:
            errors.append(f"{cid}: decisive span does not round-trip")
        target_numbers = numeric_tokens(target["span_text"])
        if not target_numbers:
            errors.append(f"{cid}: decisive span has no numeric token")

        required_values = [
            str(item.get("value", ""))
            for item in target.get("required_facts", [])
        ]
        if not required_values:
            errors.append(f"{cid}: decisive row has no required facts")
        question_numbers = numeric_tokens(case["question"])
        leaked = set().union(*(numeric_tokens(value) for value in required_values)) & question_numbers
        if leaked:
            errors.append(f"{cid}: question contains answer numeric token(s): {sorted(leaked)}")

        same_doc_hard = 0
        hard_number_sets = []
        for row in hard:
            key = (row["doc_id"], str(row["version"]))
            document = docs.get(key)
            if document is None or not document.is_retrievable:
                errors.append(f"{cid}: hard negative {key} is not retrievable")
                continue
            text = document.raw_text[row["char_start"]:row["char_end"]]
            if text != row["span_text"]:
                errors.append(f"{cid}: hard-negative span does not round-trip: {key}")
            nums = numeric_tokens(row["span_text"])
            if not nums:
                errors.append(f"{cid}: hard negative contains no numeric token: {key}")
            hard_number_sets.append(nums)
            if key == target_key:
                same_doc_hard += 1
            if row["char_start"] < target["char_end"] and target["char_start"] < row["char_end"] and key == target_key:
                errors.append(f"{cid}: hard negative overlaps decisive span in same document")
        if same_doc_hard < 1:
            errors.append(f"{cid}: needs at least one same-document numeric hard negative")

        distinct_hard_numbers = set().union(*hard_number_sets) if hard_number_sets else set()
        if target_numbers and distinct_hard_numbers and target_numbers == distinct_hard_numbers:
            errors.append(f"{cid}: hard-negative numbers do not add a distinct numeric alternative")

        overlap_rows[cid] = {
            "coverage": coverage(case["question"], target["span_text"]),
            "target_numeric_tokens": sorted(target_numbers),
            "hard_negative_numeric_tokens": sorted(distinct_hard_numbers),
        }

    for split in ("DEV", "TEST"):
        if len(split_areas[split]) < MIN_PROCESS_AREAS_PER_SPLIT:
            errors.append(
                f"{split}: repair cases cover {len(split_areas[split])} process areas; "
                f"need >= {MIN_PROCESS_AREAS_PER_SPLIT}"
            )

    observations.extend([
        f"repair_cases={len(repair_ids)}",
        f"repair_dev={split_counts['DEV']}",
        f"repair_test={split_counts['TEST']}",
        f"repair_dev_process_areas={len(split_areas['DEV'])}",
        f"repair_test_process_areas={len(split_areas['TEST'])}",
    ])

    report = {
        "status": "PASS" if not errors else "FAIL",
        "observations": observations,
        "repair_case_ids": repair_ids,
        "repair_case_diagnostics": overlap_rows,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
