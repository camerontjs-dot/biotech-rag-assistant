"""Check semantic-control structure and custody; never judge semantics or run an assessor.

Requires the pinned JSON Schema backend. No network schemas are resolved. Preparation
mode reads only this new package and four explicitly named predecessor identity files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PACKAGE = Path("research/evidence/qualifier-grounding-semantic-assessor-controls-v1")
SCHEMA_NAMES = (
    "case", "annotation", "author-design", "relations", "disagreements", "launch-receipt"
)
GUARDS = (
    "core_independently_supported", "bindings_preserved", "required_context_retained",
    "removal_independent", "no_missing_presupposition", "gap_explicit",
)
DOWNSTREAM = {
    "research/qualifier_grounding_reducer_v2/reducer.py":
        "8b56889e84660db1fc93bc29ab7fabe7fcbc12706ee15be488daab8c76baf5f7",
    "research/evidence/qualifier-grounding-policy-v2/policy.json":
        "96fcb4cb34378d768a4870f284e0d61c7f40a9f73a923170454fc9994c481f14",
    "research/evidence/qualifier-grounding-policy-v2/interface.json":
        "1ab5683435afd17976f4f093e1a07740f540fc6700e9f615b1d5fbb2e773b387",
    "research/evidence/qualifier-grounding-offline-qualification-v2/execution/TERMINAL.json":
        "47cca465586234642eed737ff51b680c7e1373fe95a2025ebc5e667ddec172de",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, ensure_ascii=False,
                          separators=(",", ":")).encode("utf-8"))


def strict_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def bad_constant(value):
    raise ValueError(f"non-JSON constant: {value}")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=strict_object,
                      parse_constant=bad_constant)


def local_schema(schema):
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key in ("$ref", "$dynamicRef"):
                require(value.startswith("#/"), "external schema reference forbidden")
            local_schema(value)
    elif isinstance(schema, list):
        for value in schema:
            local_schema(value)


def schema_check(value, schema):
    # Import physically; unavailable backend is CHECK_UNAVAILABLE, never a mock pass.
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError

    local_schema(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        raise ValueError(f"invalid schema: {error.message}") from error
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    require(not errors, "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:8]))


def unique(values, label):
    require(len(values) == len(set(values)), f"duplicate {label}")


def anchor_check(anchor, text):
    require(0 <= anchor["start"] < anchor["end"] <= len(text), "anchor range invalid")
    require(text[anchor["start"]:anchor["end"]] == anchor["text"], "anchor text mismatch")


def validate_case(case, schema):
    schema_check(case, schema)
    require(sha(case["claim"].encode()) == case["claim_sha256"], "claim hash mismatch")
    require(len(case["claim"].split()) <= 60, "claim word limit exceeded")
    require(sum(len(b["text"].split()) for b in case["authorized_body"]) <= 180,
            "BODY word limit exceeded")
    require(sum(len(b["text"].split()) for b in case["distractors"]) <= 60,
            "distractor word limit exceeded")
    unique([b["witness_id"] for b in case["authorized_body"]] +
           [d["id"] for d in case["distractors"]], "witness/distractor ID")
    for body in case["authorized_body"]:
        digest = sha(body["text"].encode())
        require(digest == body["text_sha256"] == body["source_sha256"], "BODY hash mismatch")
        require(body["source_span"] == {"start": 0, "end": len(body["text"])},
                "source span must address the complete admitted fragment")


def validate_annotation(annotation, case, schema):
    schema_check(annotation, schema)
    require(annotation["case_id"] == case["case_id"], "annotation case ID mismatch")
    require(annotation["input_sha256"] == canonical_sha(case), "annotation input hash mismatch")
    obligations = {o["id"]: o for o in annotation["obligations"]}
    unique([o["id"] for o in annotation["obligations"]], "obligation ID")
    signatures = []
    for node in obligations.values():
        for anchor in node["claim_anchors"] + node["scope_anchors"]:
            anchor_check(anchor, case["claim"])
        parent = node["parent_id"]
        if node["kind"] == "ASSERTION":
            require(parent is None, "ASSERTION parent must be null")
        else:
            require(parent in obligations and obligations[parent]["kind"] == "ASSERTION",
                    "facet must reference its ASSERTION")
        require(all(i in obligations and i != node["id"]
                    for i in node["scope_dependency_ids"]), "unknown/self scope dependency")
        signatures.append((node["kind"],
                           tuple(sorted((a["start"], a["end"]) for a in node["claim_anchors"])),
                           tuple(sorted((a["start"], a["end"]) for a in node["scope_anchors"])),
                           node["parent_id"]))
    unique(signatures, "obligation boundary signature")
    for node_id in obligations:
        pending = [(node_id, frozenset())]
        while pending:
            current, ancestors = pending.pop()
            require(current not in ancestors, "cyclic scope dependency")
            pending.extend((i, ancestors | {current})
                           for i in obligations[current]["scope_dependency_ids"])
    for item in annotation["exclusions"]:
        for anchor in item["claim_anchors"]:
            anchor_check(anchor, case["claim"])
    if annotation["coverage"] == "COMPLETE":
        require(all(o["materiality"] == "MATERIAL" for o in obligations.values()),
                "COMPLETE coverage cannot carry UNKNOWN materiality")
    else:
        require(annotation["uncertainties"], "UNKNOWN coverage needs an explicit uncertainty")
    bodies = {b["witness_id"]: b["text"] for b in case["authorized_body"]}
    seen = set()
    for row in annotation["relations"]:
        require(row["obligation_id"] in obligations, "unknown relation obligation")
        require(all(i in bodies for i in row["witness_ids"]), "nonauthoritative witness reference")
        key = row["obligation_id"], tuple(sorted(row["witness_ids"]))
        require(key not in seen, "duplicate relation row")
        seen.add(key)
        if row["relation"] != "SILENT":
            require(row["evidence"], "non-SILENT relation needs evidence")
        if row["relation"] == "AMBIGUOUS":
            require(len(row["alternatives"]) >= 2, "AMBIGUOUS needs competing readings")
        for anchor in row["evidence"]:
            require(anchor["witness_id"] in row["witness_ids"], "evidence outside witness group")
            anchor_check(anchor, bodies[anchor["witness_id"]])
        if len(row["witness_ids"]) > 1 and row["relation"] != "SILENT":
            require({e["witness_id"] for e in row["evidence"]} == set(row["witness_ids"]),
                    "joint proof needs evidence from every constituent")
    required = {(o, (b,)) for o in obligations for b in bodies}
    require(required <= seen, "missing atomic obligation/BODY relation row")
    proposal = annotation["decomposition"]
    require((case["projection"] is None) == (proposal is None), "projection applicability omitted")
    if proposal is not None:
        require(set(proposal["core_ids"] + proposal["gap_ids"]) <= set(obligations),
                "unknown projection obligation")
        require(set(proposal["body_witness_ids"]) <= set(bodies), "invalid projection witness")
        if proposal["applicability"] == "REQUIRED":
            require(set(proposal["guard_justifications"]) == set(GUARDS),
                    "every guard needs its own justification")
            for justification in proposal["guard_justifications"].values():
                for anchor in justification["claim_anchors"]:
                    anchor_check(anchor, case["claim"])
                for anchor in justification["evidence"]:
                    require(anchor["witness_id"] in bodies, "guard evidence is not BODY")
                    anchor_check(anchor, bodies[anchor["witness_id"]])
    # Semantic partition/safety/application errors are NOT assessed by this checker.


def validate_corpus(cases, design, relations, schemas, inventory):
    for case in cases:
        validate_case(case, schemas["case"])
    schema_check(design, schemas["author-design"])
    schema_check(relations, schemas["relations"])
    require(design["corpus_id"] == relations["corpus_id"] == inventory["corpus_id"],
            "corpus identity mismatch")
    unique([c["case_id"] for c in cases], "case ID")
    entries = design["entries"]
    unique([e["slot"] for e in entries], "slot")
    unique([e["case_id"] for e in entries], "design case ID")
    slots = inventory["anchors"] + inventory["invariance"] + inventory["mutations"]
    require({e["slot"] for e in entries} == {s["slot"] for s in slots}, "inventory slot mismatch")
    require(len(cases) == inventory["packet_count"] and
            {e["case_id"] for e in entries} == {c["case_id"] for c in cases},
            "case/design set mismatch")
    by_slot = {e["slot"]: e for e in entries}
    anchors = {s["category"]: by_slot[s["slot"]]["case_id"] for s in inventory["anchors"]}
    by_id = {c["case_id"]: c for c in cases}
    for spec in inventory["anchors"]:
        entry = by_slot[spec["slot"]]
        require(entry["role"] == "ANCHOR" and entry["category"] == spec["category"] and
                entry["seed_kind"] == spec["seed_kind"], "anchor assignment mismatch")
    rows = relations["relations"]
    unique([r["id"] for r in rows], "relation ID")
    specs = inventory["invariance"] + inventory["mutations"]
    require({r["id"] for r in rows} == {s["slot"] for s in specs}, "relation slot mismatch")
    for spec in specs:
        row = next(r for r in rows if r["id"] == spec["slot"])
        entry = by_slot[spec["slot"]]
        expected_role = "INVARIANT" if spec["mode"] == "INVARIANT" else "MUTATION"
        require(entry["role"] == expected_role and entry["category"] == spec["anchor_category"],
                "variant assignment mismatch")
        require(row["family"] == spec["family"] and row["mode"] == spec["mode"] and
                row["left_case_id"] == anchors[spec["anchor_category"]] and
                row["right_case_id"] == entry["case_id"], "relation endpoint/family mismatch")
        require(row["left_case_id"] != row["right_case_id"], "relation self-endpoint")
        for mapping in row["anchor_map"]:
            anchor_check(mapping["left"], by_id[row["left_case_id"]]["claim"])
            anchor_check(mapping["right"], by_id[row["right_case_id"]]["claim"])
    opportunities = {(o["guard"], o["value"]) for e in entries for o in e["guard_opportunities"]}
    require(all((guard, value) in opportunities for guard in GUARDS for value in ("TRUE", "FALSE")),
            "missing declared guard opportunity")
    require(any(value == "UNKNOWN" for _, value in opportunities),
            "missing UNKNOWN guard opportunity")


def validate_receipt(receipt, schema):
    schema_check(receipt, schema)
    if receipt["contamination_status"] == "CLEAN":
        require(not receipt["forbidden_exposures"], "CLEAN receipt has forbidden exposure")
        allowed = {(r["reference"], r["sha256"]) for r in receipt["allowed_artifacts"]}
        require(all((r["reference"], r["sha256"]) in allowed
                    for r in receipt["exposed_artifacts"]), "CLEAN receipt has unlisted exposure")
    require(receipt["counts"]["reducer_calls"] == 0 and
            receipt["counts"]["project_generation_calls"] == 0, "protected runtime call")
    if receipt["stage"] != "QUALIFICATION":
        require(receipt["counts"]["semantic_assessor_calls"] == 0,
                "semantic assessor called outside qualification")


def inside(root, reference):
    candidate = root / reference
    require(not Path(reference).is_absolute() and ".." not in Path(reference).parts,
            "unsafe manifest path")
    require(candidate.is_file() and not candidate.is_symlink(), "missing/symlink artifact")
    require(candidate.resolve().is_relative_to(root.resolve()), "artifact escapes root")
    return candidate


def check_preparation(root, require_freeze=False):
    package = root / PACKAGE
    manifest = read_json(package / "package-manifest.json")
    require(manifest["package_id"] == PACKAGE.name, "package ID mismatch")
    for reference, digest in manifest["artifacts"].items():
        require(sha(inside(root, reference).read_bytes()) == digest, f"drift: {reference}")
    for reference, digest in DOWNSTREAM.items():
        require(sha(inside(root, reference).read_bytes()) == digest,
                f"predecessor drift: {reference}")
    rubric = read_json(package / "rubric-freeze.json")
    require(sha((package / "rubric.md").read_bytes()) == rubric["rubric_sha256"], "rubric drift")
    require(rubric["commit"] == "e68ea36403c4c17c5b111e88ae1e5ca9031c1ca5" and
            rubric["tree"] == "6edf340e5e5a1201d911502292c79663faa592f7", "rubric identity drift")
    experiment = read_json(package / "EXPERIMENT.json")
    require(experiment["state"] == "designed" and experiment["execution_status"] == "NOT_RUN",
            "this preparation is not an execution receipt")
    require(all(v == "NOT_RUN" for v in experiment["stages"].values()), "stage was executed")
    require(all(type(v) is int and v == 0 for v in experiment["counts"].values()),
            "preparation call count is nonzero")
    require(experiment["wave_b"] == "LOCKED" and not experiment["protected_actions_executed"],
            "protected boundary changed")
    require(experiment["protocol_sha256"] == sha((package / "qualification.md").read_bytes()),
            "protocol binding mismatch")
    inventory = read_json(package / "case-design.json")
    require((inventory["packet_count"], inventory["anchor_count"], inventory["invariance_count"],
             inventory["mutation_count"]) == (44, 28, 8, 8), "design count drift")
    require(inventory["corpus_state"] == "FUTURE_NOT_AUTHORED" and
            inventory["accepted_labels_state"] == "FUTURE_NOT_ADJUDICATED" and
            inventory["corpus_sha256"] is None and inventory["relations_sha256"] is None and
            not inventory["case_author_launched"], "future data falsely materialized")
    for name in SCHEMA_NAMES:
        schema = read_json(package / "schemas" / f"{name}.schema.json")
        local_schema(schema)
        from jsonschema import Draft202012Validator
        from jsonschema.exceptions import SchemaError

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as error:
            raise ValueError(f"invalid schema: {error.message}") from error
    launches = sorted((package / "launches").glob("*.json"))
    require(len(launches) == 6, "six launch packets required")
    for path in launches:
        launch = read_json(path)
        require(launch["fresh_context_required"] and launch["preparation_only"] and
                not launch["launch_authorized_by_this_task"], "launch authority drift")
        for reference in launch["allowed_files"]:
            inside(package, reference)
        require(all(s["sha256"] is None and s["state"] == "NOT_MATERIALIZED"
                    for s in launch["future_slots"]), "future launch slot materialized")
        if launch["role"].startswith("ADJUDICATOR_"):
            require(set(launch["allowed_files"]) == {
                "rubric.md", "schemas/case.schema.json", "schemas/annotation.schema.json",
                "schemas/launch-receipt.schema.json"}, "adjudicator aperture widened")
    require(not any((package / name).exists() for name in
                    ("cases.jsonl", "design.json", "relations.json", "expectations.json",
                     "adjudicator-a.jsonl", "adjudicator-b.jsonl", "assessor-outputs.jsonl")),
            "qualification artifacts must not exist in preparation")
    if require_freeze:
        freeze = read_json(package / "freeze.json")
        require(sha((package / "package-manifest.json").read_bytes()) ==
                freeze["manifest_sha256"], "manifest freeze drift")
        require(freeze["terminal_state"] == "TERMINAL_PREPARATION_READY", "freeze not ready")
    return len(manifest["artifacts"]), len(launches)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true",
                        help="check preparation, no semantic execution")
    parser.add_argument("--require-freeze", action="store_true")
    parser.add_argument("--kind", choices=SCHEMA_NAMES)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--case", type=Path)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    report = {"schema_version": "semantic-structural-check/v1",
              "at_utc": datetime.now(UTC).isoformat(), "semantic_judgments_performed": 0,
              "assessor_or_adjudicator_invocations": 0, "scope": "structure and custody only"}
    try:
        if args.check:
            count, launches = check_preparation(args.root, args.require_freeze)
            report.update(status="PASS_PREPARATION_STRUCTURE_ONLY",
                          artifact_hash_checks=count, launch_packets=launches)
        else:
            require(args.kind is not None and args.input is not None, "kind/input required")
            schema_path = args.root / PACKAGE / "schemas" / f"{args.kind}.schema.json"
            schema, value = read_json(schema_path), read_json(args.input)
            if args.kind == "case":
                validate_case(value, schema)
            elif args.kind == "annotation":
                require(args.case is not None, "annotation requires its exact case")
                validate_annotation(value, read_json(args.case), schema)
            elif args.kind == "launch-receipt":
                validate_receipt(value, schema)
            else:
                schema_check(value, schema)
            report.update(status="PASS_STRUCTURE_ONLY", input_sha256=sha(args.input.read_bytes()))
        exit_code = 0
    except (ValueError, KeyError, TypeError) as error:
        report.update(status="STRUCTURAL_INVALID", error=str(error))
        exit_code = 1
    except (ImportError, OSError) as error:
        report.update(status="CHECK_UNAVAILABLE", error=str(error))
        exit_code = 2
    with args.receipt.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
