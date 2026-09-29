#!/usr/bin/env python3
"""Check whether the sealed v2 PROSPECTIVE set can qualify as v2.1 numeric-collision evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus

NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?")
MIN_B04_CASES = 4
MIN_PROCESS_AREAS = 2


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def prospective_digest(root: Path) -> str:
    files = sorted(path for path in root.iterdir() if path.is_file())
    listing = "".join(
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n"
        for path in files
    )
    return hashlib.sha256(listing.encode()).hexdigest()


def normalize_families(raw: object) -> dict[str, dict]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {row["case_id"]: row for row in raw}
    raise TypeError("families.json must be an object or list")


def numbers(text: str) -> set[str]:
    return set(NUMBER_RE.findall(text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--prospective", type=Path, required=True)
    parser.add_argument("--v2-freeze", type=Path, required=True)
    args = parser.parse_args()

    benchmark = args.benchmark.resolve()
    prospective = args.prospective.resolve()
    freeze = json.loads(args.v2_freeze.read_text(encoding="utf-8"))
    expected_digest = freeze["prospective_sha256"]
    observed_digest = prospective_digest(prospective)

    cases = {row["case_id"]: row for row in jsonl(prospective / "cases.jsonl")}
    gold_rows = jsonl(prospective / "gold.jsonl")
    families = normalize_families(
        json.loads((prospective / "families.json").read_text(encoding="utf-8"))
    )
    gold: dict[str, list[dict]] = defaultdict(list)
    for row in gold_rows:
        gold[row["case_id"]].append(row)

    corpus = load_corpus(benchmark / "corpus")
    docs = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }

    b04_ids = sorted(
        case_id
        for case_id, info in families.items()
        if info.get("family") == "B04"
    )
    process_areas: set[str] = set()
    case_results: dict[str, dict] = {}

    for case_id in b04_ids:
        errors: list[str] = []
        case = cases.get(case_id)
        info = families.get(case_id, {})
        spans = gold.get(case_id, [])
        if case is None:
            errors.append("missing runtime case")
            case_results[case_id] = {"qualifies": False, "errors": errors}
            continue

        process_areas.add(info.get("process_area", ""))
        decisive = [row for row in spans if row.get("decisive")]
        hard = [
            row
            for row in spans
            if row.get("relevance_class") == "hard_negative"
        ]
        dispositions = {row.get("expected_disposition") for row in spans}

        if dispositions != {"answer"}:
            errors.append(f"disposition is {sorted(dispositions)}")
        if len(decisive) != 1:
            errors.append(f"decisive span count is {len(decisive)}")
        if len(hard) < 3:
            errors.append(f"hard-negative count is {len(hard)}")

        same_document_hard = 0
        if decisive:
            target = decisive[0]
            target_key = (target.get("doc_id"), str(target.get("version")))
            target_doc = docs.get(target_key)
            if target_doc is None or not target_doc.is_retrievable:
                errors.append("decisive span is not retrievable")
            else:
                text = target_doc.raw_text[
                    target["char_start"] : target["char_end"]
                ]
                if text != target.get("span_text"):
                    errors.append("decisive span does not round-trip")
                target_numbers = numbers(text)
                if not target_numbers:
                    errors.append("decisive span has no numeric token")

                values = [
                    str(item.get("value", ""))
                    for item in target.get("required_facts", [])
                ]
                answer_numbers = set().union(
                    *(numbers(value) for value in values)
                )
                leaked = answer_numbers & numbers(case["question"])
                if leaked:
                    errors.append(
                        f"question leaks answer numeric token(s): {sorted(leaked)}"
                    )

                hard_numbers: set[str] = set()
                for row in hard:
                    key = (row.get("doc_id"), str(row.get("version")))
                    document = docs.get(key)
                    if document is None or not document.is_retrievable:
                        errors.append(f"hard negative {key} is not retrievable")
                        continue
                    hard_text = document.raw_text[
                        row["char_start"] : row["char_end"]
                    ]
                    if hard_text != row.get("span_text"):
                        errors.append(f"hard negative {key} does not round-trip")
                    nums = numbers(hard_text)
                    if not nums:
                        errors.append(f"hard negative {key} has no numeric token")
                    hard_numbers.update(nums)
                    if key == target_key:
                        same_document_hard += 1

                if same_document_hard < 1:
                    errors.append("no same-document numeric hard negative")
                if target_numbers and hard_numbers == target_numbers:
                    errors.append(
                        "hard negatives add no distinct numeric alternative"
                    )

        case_results[case_id] = {
            "qualifies": not errors,
            "hard_negative_count": len(hard),
            "same_document_hard_negative_count": same_document_hard,
            "errors": errors,
        }

    all_b04_qualify = bool(b04_ids) and all(
        row["qualifies"] for row in case_results.values()
    )
    enough_cases = len(b04_ids) >= MIN_B04_CASES
    enough_areas = len(process_areas - {""}) >= MIN_PROCESS_AREAS
    commitment_match = observed_digest == expected_digest

    qualifies = (
        commitment_match
        and enough_cases
        and enough_areas
        and all_b04_qualify
    )
    disposition = (
        "EXISTING_PROSPECTIVE_QUALIFIES_V21"
        if qualifies
        else "NEW_V21_PROSPECTIVE_REQUIRED"
    )
    report = {
        "disposition": disposition,
        "commitment_match": commitment_match,
        "expected_prospective_sha256": expected_digest,
        "observed_prospective_sha256": observed_digest,
        "b04_cases": len(b04_ids),
        "b04_case_ids": b04_ids,
        "process_areas": sorted(process_areas - {""}),
        "all_b04_qualify": all_b04_qualify,
        "case_results": case_results,
        "non_claims": [
            "This check runs no retrieval model.",
            "A qualifying result establishes only v2.1 structural numeric-collision coverage.",
            "A non-qualifying result does not invalidate the historical v2 prospective set.",
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if qualifies else 2


if __name__ == "__main__":
    raise SystemExit(main())
