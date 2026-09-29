#!/usr/bin/env python3
"""Structural acceptance for a sealed controlled-docs-v2.1 PROSPECTIVE set."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from biotech_rag_assistant.corpus import load_corpus
from biotech_rag_assistant.retrieval import coverage

FILES = ("cases.jsonl", "families.json", "gold.jsonl")
PROCESS_AREAS = {
    "complaints-and-returns",
    "document-control",
    "training-and-gowning-qualification",
}
FAMILY_COUNTS = {
    "B01": 2,
    "B02": 4,
    "B03": 2,
    "B04": 4,
    "B05": 2,
    "B06": 2,
    "B07": 1,
    "B08": 2,
    "B09": 2,
    "B10": 3,
    "B11": 2,
    "B12": 2,
    "B13": 1,
    "B14": 1,
}
EXPECTED_IDS = [f"C-PROS21-{index:04d}" for index in range(1, 31)]
RUNTIME_FIELDS = {
    "case_id",
    "split",
    "question",
    "query_style",
    "aperture_id",
    "top_k",
    "schema_version",
}
NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?")
IDENTIFIER_RE = re.compile(r"\b[A-Z]{2,}(?:-[A-Z0-9]+)+\b")


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def numeric_tokens(text: str) -> set[str]:
    return set(NUMBER_RE.findall(text))


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def commitment(root: Path) -> tuple[str, dict[str, str]]:
    hashes = {name: file_sha256(root / name) for name in FILES}
    listing = "".join(f"{hashes[name]}  {name}\n" for name in sorted(FILES))
    return hashlib.sha256(listing.encode()).hexdigest(), hashes


def check_file_format(path: Path, errors: list[str]) -> None:
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        errors.append(f"{path.name}: UTF-8 BOM is not allowed")
    if b"\r\n" in data or b"\r" in data:
        errors.append(f"{path.name}: CR/CRLF line endings are not allowed")
    if data and not data.endswith(b"\n"):
        errors.append(f"{path.name}: final LF is required")


def roundtrip(row: dict, documents: dict[tuple[str, str], object]) -> tuple[object | None, str]:
    doc_id = row.get("doc_id")
    version = row.get("version")
    start = row.get("char_start")
    end = row.get("char_end")
    span_text = row.get("span_text")
    if doc_id is None:
        return None, ""
    key = (doc_id, str(version))
    document = documents.get(key)
    if document is None:
        return None, f"unknown document/version {key}"
    if not isinstance(start, int) or not isinstance(end, int):
        return document, "non-null document requires integer offsets"
    if start < 0 or end <= start or end > len(document.raw_text):
        return document, f"invalid offsets {start}:{end}"
    observed = document.raw_text[start:end]
    if observed != span_text:
        return document, "span_text does not round-trip"
    return document, ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--prospective", type=Path, required=True)
    args = parser.parse_args()

    benchmark = args.benchmark.resolve()
    prospective = args.prospective.resolve()
    errors: list[str] = []

    actual_files = sorted(
        path.name for path in prospective.iterdir() if path.is_file()
    )
    if actual_files != sorted(FILES):
        errors.append(
            f"sealed directory must contain exactly {list(FILES)}; found {actual_files}"
        )
    for name in FILES:
        path = prospective / name
        if path.exists():
            check_file_format(path, errors)

    cases_rows = jsonl(prospective / "cases.jsonl")
    families_raw = json.loads(
        (prospective / "families.json").read_text(encoding="utf-8")
    )
    gold_rows = jsonl(prospective / "gold.jsonl")

    if not isinstance(families_raw, dict):
        errors.append("families.json must be an object keyed by case_id")
        families: dict[str, dict] = {}
    else:
        families = families_raw

    case_ids = [row.get("case_id") for row in cases_rows]
    if case_ids != EXPECTED_IDS:
        errors.append(
            "case IDs must be exactly C-PROS21-0001 through C-PROS21-0030 "
            "in ascending order"
        )
    if len(set(case_ids)) != len(case_ids):
        errors.append("duplicate case_id in cases.jsonl")
    if set(families) != set(EXPECTED_IDS):
        errors.append("families.json keys must exactly match the 30 prospective IDs")

    cases = {row["case_id"]: row for row in cases_rows if "case_id" in row}
    gold: dict[str, list[dict]] = defaultdict(list)
    for row in gold_rows:
        case_id = row.get("case_id")
        if case_id not in cases:
            errors.append(f"gold row refers to unknown case {case_id}")
        else:
            gold[case_id].append(row)
    missing_gold = [case_id for case_id in EXPECTED_IDS if not gold[case_id]]
    if missing_gold:
        errors.append(f"cases without gold rows: {missing_gold}")

    committed_questions: set[str] = set()
    committed_areas: set[str] = set()
    for split in ("dev", "test"):
        for row in jsonl(benchmark / "cases" / f"{split}_cases.jsonl"):
            committed_questions.add(row["question"].strip().lower())
        committed_families = json.loads(
            (benchmark / "evaluator_only/families.json").read_text(
                encoding="utf-8"
            )
        )
        committed_areas.update(
            value["process_area"] for value in committed_families.values()
        )

    corpus = load_corpus(benchmark / "corpus")
    documents = {
        (doc.metadata.doc_id, doc.metadata.version): doc
        for doc in corpus.documents
    }
    manifest = json.loads(
        (benchmark / "corpus_manifest.json").read_text(encoding="utf-8")
    )
    process_area_by_doc = {
        (row["doc_id"], str(row["version"])): row["process_area"]
        for row in manifest["documents"]
    }

    family_counts: Counter[str] = Counter()
    process_counts: Counter[str] = Counter()
    style_counts: Counter[str] = Counter()
    questions: Counter[str] = Counter()
    b04_receipt: dict[str, dict] = {}

    for case_id in EXPECTED_IDS:
        case = cases.get(case_id)
        family = families.get(case_id)
        spans = gold.get(case_id, [])
        if case is None or family is None:
            continue

        if set(case) != RUNTIME_FIELDS:
            errors.append(
                f"{case_id}: runtime fields differ from schema: {sorted(case)}"
            )
        if case.get("split") != "PROSPECTIVE":
            errors.append(f"{case_id}: split must be PROSPECTIVE")
        if case.get("aperture_id") != "full":
            errors.append(f"{case_id}: aperture_id must be full")
        if case.get("top_k") != 3:
            errors.append(f"{case_id}: top_k must be 3")
        if case.get("schema_version") != "2.1":
            errors.append(f"{case_id}: schema_version must be 2.1")
        if case.get("query_style") not in {"natural", "keyword", "identifier"}:
            errors.append(f"{case_id}: invalid query_style")

        question_key = case["question"].strip().lower()
        questions[question_key] += 1
        if question_key in committed_questions:
            errors.append(f"{case_id}: question duplicates committed DEV/TEST text")

        family_code = family.get("family")
        area = family.get("process_area")
        family_counts[family_code] += 1
        process_counts[area] += 1
        style_counts[case["query_style"]] += 1

        if family.get("case_id") != case_id:
            errors.append(f"{case_id}: family record case_id mismatch")
        if area not in PROCESS_AREAS:
            errors.append(f"{case_id}: disallowed process area {area}")
        if area in committed_areas:
            errors.append(f"{case_id}: prospective process area appears in DEV/TEST")

        dispositions = {row.get("expected_disposition") for row in spans}
        if len(dispositions) != 1:
            errors.append(f"{case_id}: mixed expected dispositions {dispositions}")
            continue
        disposition = next(iter(dispositions))
        decisive = [row for row in spans if row.get("decisive")]
        hard = [
            row for row in spans
            if row.get("relevance_class") == "hard_negative"
        ]

        for row in spans:
            document, issue = roundtrip(row, documents)
            if issue:
                errors.append(f"{case_id}: {issue}")
                continue
            if document is not None:
                key = (document.metadata.doc_id, document.metadata.version)
                row_area = process_area_by_doc.get(key)
                if (
                    row.get("relevance_class") != "stale_trap"
                    and row_area != area
                    and family_code != "B11"
                ):
                    errors.append(
                        f"{case_id}: gold process area {row_area} differs from {area}"
                    )

        if disposition == "answer" and not decisive:
            errors.append(f"{case_id}: answer case has no decisive span")
        if disposition == "not_stated" and decisive:
            errors.append(f"{case_id}: not_stated case has decisive evidence")
        if disposition == "refusal" and decisive:
            errors.append(f"{case_id}: refusal case has decisive evidence")

        if family_code == "B01" and decisive:
            joined = "\n".join(row["span_text"] for row in decisive)
            if coverage(case["question"], joined) < 0.60:
                errors.append(f"{case_id}: B01 coverage is below 0.60")

        if family_code == "B02" and decisive:
            joined = "\n".join(row["span_text"] for row in decisive)
            if coverage(case["question"], joined) > 0.30:
                errors.append(f"{case_id}: B02 coverage is above 0.30")

        if family_code == "B03":
            if (
                case["query_style"] != "identifier"
                and not IDENTIFIER_RE.search(case["question"])
            ):
                errors.append(f"{case_id}: B03 lacks an identifier-led query")

        if family_code == "B04":
            if len(decisive) != 1:
                errors.append(
                    f"{case_id}: B04 requires exactly one decisive span"
                )
                continue
            target = decisive[0]
            target_doc, issue = roundtrip(target, documents)
            if issue or target_doc is None:
                continue
            if not target_doc.is_retrievable:
                errors.append(f"{case_id}: B04 decisive source is not retrievable")
            target_numbers = numeric_tokens(target["span_text"])
            if not target_numbers:
                errors.append(f"{case_id}: B04 decisive span has no numeric token")
            required_values = [
                str(item.get("value", ""))
                for item in target.get("required_facts", [])
            ]
            answer_numbers = set().union(
                *(numeric_tokens(value) for value in required_values)
            )
            leaked = answer_numbers & numeric_tokens(case["question"])
            if leaked:
                errors.append(
                    f"{case_id}: question leaks answer number(s) {sorted(leaked)}"
                )
            if len(hard) < 3:
                errors.append(
                    f"{case_id}: B04 needs >=3 hard negatives; found {len(hard)}"
                )
            same_doc = 0
            hard_numbers: set[str] = set()
            for row in hard:
                document, hard_issue = roundtrip(row, documents)
                if hard_issue or document is None:
                    continue
                if not document.is_retrievable:
                    errors.append(
                        f"{case_id}: B04 hard negative is not retrievable"
                    )
                nums = numeric_tokens(row["span_text"])
                if not nums:
                    errors.append(
                        f"{case_id}: B04 hard negative has no numeric token"
                    )
                hard_numbers.update(nums)
                if (
                    document.metadata.doc_id == target_doc.metadata.doc_id
                    and document.metadata.version == target_doc.metadata.version
                ):
                    same_doc += 1
            if same_doc < 1:
                errors.append(
                    f"{case_id}: B04 has no same-document numeric hard negative"
                )
            if target_numbers and hard_numbers == target_numbers:
                errors.append(
                    f"{case_id}: B04 hard negatives add no distinct numeric alternative"
                )
            b04_receipt[case_id] = {
                "hard_negative_count": len(hard),
                "same_document_hard_negative_count": same_doc,
            }

        if family_code == "B05" and decisive:
            if not any("|" in row["span_text"] for row in decisive):
                errors.append(f"{case_id}: B05 decisive evidence is not tabular")

        if family_code == "B06" and decisive:
            text = " ".join(row["span_text"].lower() for row in decisive)
            markers = ("unless", "except", "only if", " if ", " when ", "where ")
            if not any(marker in f" {text} " for marker in markers):
                errors.append(f"{case_id}: B06 lacks an explicit condition/exception")

        if family_code == "B07" and decisive:
            text = " ".join(row["span_text"].lower() for row in decisive)
            markers = (" not ", "must not", "never", "no ")
            if not any(marker in f" {text} " for marker in markers):
                errors.append(f"{case_id}: B07 lacks explicit negative polarity")

        if family_code == "B08":
            joint = [
                row for row in decisive
                if row.get("joint_group_id") is not None
            ]
            if len(joint) < 2:
                errors.append(
                    f"{case_id}: B08 requires >=2 joint decisive passages"
                )
            elif len({row["joint_group_id"] for row in joint}) != 1:
                errors.append(f"{case_id}: B08 decisive joint group is inconsistent")

        if family_code == "B09":
            stale = [
                row for row in spans
                if row.get("relevance_class") == "stale_trap"
            ]
            if not stale:
                errors.append(f"{case_id}: B09 has no stale_trap evidence")
            for row in stale:
                document, issue = roundtrip(row, documents)
                if issue or document is None:
                    continue
                if document.is_retrievable:
                    errors.append(f"{case_id}: B09 stale trap is retrievable")

        if family_code == "B10":
            if disposition != "not_stated":
                errors.append(f"{case_id}: B10 disposition must be not_stated")
            material = [
                row for row in spans
                if row.get("relevance_class")
                in {"material_context", "hard_negative"}
            ]
            if not material:
                errors.append(f"{case_id}: B10 has no material context")

        if family_code == "B11" and disposition != "refusal":
            errors.append(f"{case_id}: B11 disposition must be refusal")

        if family_code == "B12" and not hard:
            errors.append(f"{case_id}: B12 has no hard_negative evidence")

        if family_code == "B13":
            if not decisive:
                errors.append(f"{case_id}: B13 has no decisive governing evidence")
            training_conflicts = 0
            for row in hard:
                document, issue = roundtrip(row, documents)
                if issue or document is None:
                    continue
                if document.metadata.doc_type == "TrainingNote":
                    training_conflicts += 1
            if training_conflicts < 1:
                errors.append(
                    f"{case_id}: B13 needs a TrainingNote hard negative"
                )

        if family_code == "B14" and decisive:
            qualifying = False
            for row in decisive:
                document, issue = roundtrip(row, documents)
                if issue or document is None:
                    continue
                if (
                    document.metadata.doc_type == "SOP"
                    and len(document.raw_text.split()) >= 3500
                ):
                    qualifying = True
            if not qualifying:
                errors.append(
                    f"{case_id}: B14 decisive evidence is not in a >=3500-word SOP"
                )

    duplicate_questions = [
        question for question, count in questions.items() if count > 1
    ]
    if duplicate_questions:
        errors.append(f"duplicate prospective questions: {duplicate_questions}")

    if family_counts != Counter(FAMILY_COUNTS):
        errors.append(
            f"family counts differ: observed {dict(family_counts)} "
            f"expected {FAMILY_COUNTS}"
        )
    expected_process = Counter({area: 10 for area in PROCESS_AREAS})
    if process_counts != expected_process:
        errors.append(
            f"process-area counts differ: observed {dict(process_counts)} "
            f"expected {dict(expected_process)}"
        )
    if style_counts["natural"] < 15:
        errors.append("need at least 15 natural questions")
    if style_counts["keyword"] < 5:
        errors.append("need at least 5 keyword questions")
    if style_counts["identifier"] < 5:
        errors.append("need at least 5 identifier-led questions")

    digest, hashes = commitment(prospective)
    disposition = (
        "PASS_FOR_V21_PROSPECTIVE_SEAL"
        if not errors
        else "BLOCK_V21_PROSPECTIVE_SEAL"
    )
    report = {
        "disposition": disposition,
        "commitment_sha256": digest,
        "file_sha256": hashes,
        "case_count": len(cases_rows),
        "family_counts": dict(sorted(family_counts.items())),
        "process_area_counts": dict(sorted(process_counts.items())),
        "query_style_counts": dict(sorted(style_counts.items())),
        "b04": b04_receipt,
        "errors": errors,
        "non_claims": [
            "This checker runs no retrieval model.",
            "A pass establishes structural prospective-set acceptance only.",
            "The sealed set remains unevaluated against candidate retrieval systems.",
        ],
    }
    print(json.dumps(report, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
