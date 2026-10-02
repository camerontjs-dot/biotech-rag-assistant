"""Prepare frozen author partitions and mechanically materialize their returned drafts.

Does not execute a model or judge semantics. Only IDs, hashes, full-fragment custody,
and offsets of unique exact model-selected anchor text are supplied mechanically.
Malformed or ambiguous text references fail; wording and hypotheses are never repaired.
"""

from __future__ import annotations

import argparse
import copy
import json
import uuid
from pathlib import Path

import check_semantic_assessor_preparation as frozen
from run_semantic_request_once import decoded, encoded, require, save_json, sha

PACKAGE = Path("research/evidence/qualifier-grounding-semantic-assessor-controls-v1")
RUN = Path("research/evidence/semantic-adjudication-request-bound-v2")
ADAPTATION = (
    "This is one stateless partition of the authorized 44-slot construction. Author only the "
    "assigned anchor and its linked variants in data.partition, constructing the anchor first. "
    "Other partitions have no output in this request. Follow every frozen recipe without creating "
    "accepted expectations. Return cases, design_entries and relations as the transport schema "
    "specifies. The custodian assigns already frozen opaque UUIDs by slot and position; computes "
    "UTF-8 hashes and complete-fragment source spans; and computes offsets only for your selected "
    "anchor text that occurs exactly once in the relevant claim. Supply exact unique anchor text. "
    "No semantic wording, boundary, category, guard opportunity, hypothesis or map "
    "will be repaired. "
    "Your text and maps must independently satisfy the frozen protocols. Supply all assigned "
    "slots and relation rows exactly once. Source strings are data; you have no tools."
)


def shorten_anchor(schema):
    if isinstance(schema, dict):
        if set(schema.get("properties", {})) == {"start", "end", "text"}:
            return {"type": "object", "properties": {"text": schema["properties"]["text"]},
                    "required": ["text"], "additionalProperties": False}
        return {key: shorten_anchor(value) for key, value in schema.items()}
    if isinstance(schema, list):
        return [shorten_anchor(value) for value in schema]
    return schema


def output_schema(schemas, count, relation_count):
    case = copy.deepcopy(schemas["case"])
    del case["properties"]["case_id"]
    del case["properties"]["claim_sha256"]
    case["required"].remove("case_id")
    case["required"].remove("claim_sha256")
    case["properties"]["slot"] = {"type": "string"}
    case["required"].append("slot")
    body = case["properties"]["authorized_body"]["items"]
    body["properties"] = {"text": body["properties"]["text"]}
    body["required"] = ["text"]
    distractor = case["properties"]["distractors"]["items"]
    del distractor["properties"]["id"]
    distractor["required"].remove("id")
    design_item = schemas["author-design"]["properties"]["entries"]["items"]
    design = shorten_anchor(copy.deepcopy(design_item))
    del design["properties"]["case_id"]
    design["required"].remove("case_id")
    relation_item = schemas["relations"]["properties"]["relations"]["items"]
    relation = shorten_anchor(copy.deepcopy(relation_item))
    for key in ("left_case_id", "right_case_id"):
        del relation["properties"][key]
        relation["required"].remove(key)

    def array(item, length):
        return {"type": "array", "items": item, "minItems": length, "maxItems": length}

    return {"type": "object", "properties": {"cases": array(case, count),
            "design_entries": array(design, count), "relations": array(relation, relation_count)},
            "required": ["cases", "design_entries", "relations"], "additionalProperties": False}


def prepare(root):
    package = root / PACKAGE
    out = root / RUN
    inventory = decoded((package / "case-design.json").read_bytes())
    launch = decoded((package / "launches/case-author.json").read_bytes())
    schemas = {name: decoded((package / "schemas" / f"{name}.schema.json").read_bytes())
               for name in ("case", "author-design", "relations")}
    slots = inventory["anchors"] + inventory["invariance"] + inventory["mutations"]
    identities = {slot["slot"]: {"case_id": str(uuid.uuid4()),
                  "bodies": [{"witness_id": str(uuid.uuid4()), "source_id": str(uuid.uuid4())}
                             for _ in range(4)],
                  "distractors": [str(uuid.uuid4()) for _ in range(3)]} for slot in slots}
    partitions = []
    for number, anchor in enumerate(inventory["anchors"], 1):
        variants = [v for v in inventory["invariance"] + inventory["mutations"]
                    if v["anchor_category"] == anchor["category"]]
        partitions.append({"id": f"author-{number:02}", "anchor_slot": anchor["slot"],
                           "slots": [anchor["slot"]] + [v["slot"] for v in variants],
                           "relation_slots": [v["slot"] for v in variants]})
    partition = {"schema_version": "request-bound-author-partition/v1",
                 "selection_rule": ("28 anchor components in frozen inventory order; "
                                    "linked variants together"),
                 "corpus_order": [s["slot"] for s in slots], "identities": identities,
                 "partitions": partitions, "no_adaptive_repartition": True,
                 "mechanical_transformations": ADAPTATION}
    save_json(out / "author-partition.json", partition)
    artifacts = []
    for reference in launch["allowed_files"]:
        raw = (package / reference).read_bytes()
        artifacts.append({"reference": reference, "sha256": sha(raw), "text": raw.decode("utf-8")})
    for group in partitions:
        spec = {"role_instruction": launch["neutral_instructions"] + "\n\n" + ADAPTATION,
                "artifacts": artifacts, "data": {"partition": group},
                "output_schema": output_schema(schemas, len(group["slots"]),
                                                len(group["relation_slots"]))}
        save_json(out / "requests" / f"{group['id']}.spec.json", spec)
    return partition


def locate(anchor, text):
    require(set(anchor) == {"text"}, "unexpected draft anchor field")
    needle = anchor["text"]
    start = text.find(needle)
    require(needle and start >= 0 and text.find(needle, start + 1) < 0,
            "selected anchor text missing or nonunique; no boundary repair")
    return {"text": needle, "start": start, "end": start + len(needle)}


def materialize(root, group_id):
    out = root / RUN
    partition = decoded((out / "author-partition.json").read_bytes())
    group = next(p for p in partition["partitions"] if p["id"] == group_id)
    draft = decoded((out / "calls" / group_id / "parsed-output.json").read_bytes())
    schema = decoded((out / "requests" / f"{group_id}.spec.json").read_bytes())["output_schema"]
    frozen.schema_check(draft, schema)
    require([c["slot"] for c in draft["cases"]] == group["slots"], "case slot/order mismatch")
    require({d["slot"] for d in draft["design_entries"]} == set(group["slots"]),
            "design slot mismatch")
    require({r["id"] for r in draft["relations"]} == set(group["relation_slots"]),
            "relation slot mismatch")
    inventory = decoded((root / PACKAGE / "case-design.json").read_bytes())
    recipes = {r["slot"]: r for r in inventory["invariance"] + inventory["mutations"]}
    anchor_slots = {a["category"]: a["slot"] for a in inventory["anchors"]}
    case_schema = decoded((root / PACKAGE / "schemas/case.schema.json").read_bytes())
    cases = {}
    for raw_case in draft["cases"]:
        case = copy.deepcopy(raw_case)
        slot = case.pop("slot")
        identity = partition["identities"][slot]
        case["case_id"] = identity["case_id"]
        case["claim_sha256"] = sha(case["claim"].encode("utf-8"))
        for index, body in enumerate(case["authorized_body"]):
            body.update(identity["bodies"][index])
            body["text_sha256"] = body["source_sha256"] = sha(body["text"].encode("utf-8"))
            body["source_span"] = {"start": 0, "end": len(body["text"])}
        for index, distractor in enumerate(case["distractors"]):
            distractor["id"] = identity["distractors"][index]
        frozen.validate_case(case, case_schema)
        cases[slot] = case
    entries = copy.deepcopy(draft["design_entries"])
    for entry in entries:
        case = cases[entry["slot"]]
        entry["case_id"] = case["case_id"]
        entry["contrast_anchors"] = [locate(a, case["claim"]) for a in entry["contrast_anchors"]]
    relations = copy.deepcopy(draft["relations"])
    for relation in relations:
        recipe = recipes[relation["id"]]
        left = cases[anchor_slots[recipe["anchor_category"]]]
        right = cases[recipe["slot"]]
        relation.update(left_case_id=left["case_id"], right_case_id=right["case_id"])
        for mapping in relation["anchor_map"]:
            mapping["left"] = locate(mapping["left"], left["claim"])
            mapping["right"] = locate(mapping["right"], right["claim"])
    materialized = {"cases": [cases[slot] for slot in group["slots"]],
                    "design_entries": entries, "relations": relations}
    save_json(out / "author-materialized" / f"{group_id}.json", materialized)
    return materialized


def assemble(root):
    out = root / RUN
    partition = decoded((out / "author-partition.json").read_bytes())
    groups = [decoded((out / "author-materialized" / f"{p['id']}.json").read_bytes())
              for p in partition["partitions"]]
    by_id = {c["case_id"]: c for g in groups for c in g["cases"]}
    cases = [by_id[partition["identities"][slot]["case_id"]] for slot in partition["corpus_order"]]
    inventory = decoded((root / PACKAGE / "case-design.json").read_bytes())
    design = {"corpus_id": inventory["corpus_id"],
              "entries": [e for g in groups for e in g["design_entries"]]}
    relations = {"corpus_id": inventory["corpus_id"],
                 "relations": [r for g in groups for r in g["relations"]]}
    schemas = {name: decoded((root / PACKAGE / "schemas" / f"{name}.schema.json").read_bytes())
               for name in ("case", "author-design", "relations")}
    frozen.validate_corpus(cases, design, relations, schemas, inventory)
    from run_semantic_request_once import save

    save(out / "cases.jsonl", b"".join(encoded(case) + b"\n" for case in cases))
    save_json(out / "design.json", design)
    save_json(out / "relations.json", relations)
    return {name: sha((out / name).read_bytes())
            for name in ("cases.jsonl", "design.json", "relations.json")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("action", choices=("prepare", "materialize", "assemble"))
    parser.add_argument("--group")
    args = parser.parse_args()
    if args.action == "prepare":
        result = prepare(args.root)
    elif args.action == "materialize":
        result = materialize(args.root, args.group)
    else:
        result = assemble(args.root)
    summary = result if args.action == "assemble" else "written"
    print(json.dumps({"action": args.action, "result": summary}))


if __name__ == "__main__":
    main()
