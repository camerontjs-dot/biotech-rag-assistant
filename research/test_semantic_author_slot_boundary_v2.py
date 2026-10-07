"""Uninterpreted structural tokens and fake HTTP only; zero semantic/provider evidence."""

from __future__ import annotations

import contextlib
import copy
import io
import shutil
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

import build_semantic_author_requests as predecessor
import check_semantic_assessor_preparation as frozen
import run_semantic_request_once as once
import semantic_author_slot_boundary_v1 as reference
import semantic_author_slot_boundary_v2 as boundary
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"model": "structural-token", "model_digest": "a" * 64,
          "provider_version": "test-only", "timeout_seconds": 1,
          "options": {"temperature": 0, "seed": 37, "num_ctx": 1000000, "num_predict": 64}}


def token_draft(group, inventory):
    """Shape fixture only: declarations carry NO semantic correctness or source authority."""
    draft = {"cases": [], "design_entries": [], "relations": []}
    for slot in group["slots"]:
        draft["cases"].append({"slot": slot, "claim": f"token-{slot}",
                               "authorized_body": [{"text": "body-token"}],
                               "distractors": [], "projection": None})
        entry = boundary.expected_assignment(slot, inventory)
        entry.setdefault("seed_kind", "explicit")
        draft["design_entries"].append({**entry, "guard_opportunities": [
            {"guard": guard, "value": value} for guard in frozen.GUARDS
            for value in ("TRUE", "FALSE", "UNKNOWN")],
            "author_hypothesis": "UNINTERPRETED STRUCTURAL TOKEN; NOT A SEMANTIC CONTROL",
            "contrast_anchors": [{"text": f"token-{slot}"}]})
    recipes = {row["slot"]: row for row in inventory["invariance"] + inventory["mutations"]}
    for slot in group["relation_slots"]:
        draft["relations"].append({"id": slot, "family": recipes[slot]["family"],
                                   "mode": recipes[slot]["mode"], "left_slot": group["anchor_slot"],
                                   "right_slot": slot, "dimensions": ["uninterpreted-token"],
                                   "anchor_map": [{"left": {
                                       "text": f"token-{group['anchor_slot']}"},
                                                   "right": {"text": f"token-{slot}"},
                                                   "kind": "ASSERTION"}],
                                   "changed_ranges": [], "hypothesis": "UNINTERPRETED TOKEN"})
    return draft


class Structure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory, cls.partition, cls.schemas = boundary.authority(ROOT)
        cls.group = cls.partition["partitions"][0]

    def materialize(self, draft, group=None):
        return boundary.materialize(draft, group or self.group, self.inventory,
                                    self.partition, self.schemas)

    def test_whole_plan_exact_membership_order_and_identity(self):
        self.assertEqual(boundary.validate_plan(self.partition, self.inventory),
                         {"partitions": 28, "cases": 44, "relations": 16})
        changes = [
            lambda p: p["partitions"].pop(),
            lambda p: p["partitions"].append(p["partitions"][0]),
            lambda p: p["partitions"].reverse(),
            lambda p: p["partitions"][0]["slots"].reverse(),
            lambda p: p["partitions"][0]["slots"].__setitem__(1, "anchor_02"),
            lambda p: p["partitions"][0]["relation_slots"].pop(),
            lambda p: p["corpus_order"].reverse(),
            lambda p: p["corpus_order"].__setitem__(1, "anchor_01"),
            lambda p: p["identities"].pop("anchor_02"),
            lambda p: p["identities"]["anchor_02"].__setitem__(
                "case_id", p["identities"]["anchor_01"]["case_id"]),
            lambda p: p["identities"]["anchor_01"]["bodies"][0].__setitem__(
                "source_id", p["identities"]["anchor_01"]["case_id"]),
            lambda p: p["identities"]["anchor_01"]["distractors"].__setitem__(0, "meaningful-id"),
            lambda p: p.__setitem__("no_adaptive_repartition", False),
        ]
        for number, mutate in enumerate(changes):
            with self.subTest(mutation=number), self.assertRaises(ValueError):
                plan = copy.deepcopy(self.partition)
                mutate(plan)
                boundary.validate_plan(plan, self.inventory)

    def test_historical_44_rows_33_unique_shape_is_rejected_prospectively(self):
        # #51 root-slot-verification.json at 7556badf...; only its slot vector is reproduced.
        # The natural-language outputs are not copied or relabeled as valid controls.
        historical_wrong = {
            "author-01": [f"anchor_{number:02}" for number in range(1, 8)],
            "author-09": ["anchor_09", "anchor_09"],
            "author-10": ["anchor_10", "anchor_10"],
            "author-12": ["anchor_12", "anchor_12"],
            "author-16": ["anchor_16", "anchor_16"],
            "author-18": ["anchor_18", "anchor_18"],
        }
        rows = []
        rejected = []
        for group in self.partition["partitions"]:
            draft = token_draft(group, self.inventory)
            for row, slot in zip(draft["cases"], historical_wrong.get(group["id"], group["slots"]),
                                 strict=True):
                row["slot"] = slot
                rows.append(slot)
            old = copy.deepcopy(draft)
            for relation in old["relations"]:
                relation.pop("left_slot")
                relation.pop("right_slot")
            frozen.schema_check(old, predecessor.output_schema(
                self.schemas, len(group["slots"]), len(group["relation_slots"])))
            try:
                self.materialize(draft, group)
            except ValueError:
                rejected.append(group["id"])
        counts = Counter(rows)
        self.assertEqual((len(rows), len(counts)), (44, 33))
        self.assertEqual(sum(count - 1 for count in counts.values()), 11)
        self.assertEqual(len(set(self.partition["corpus_order"]) - set(rows)), 11)
        self.assertEqual(rejected, list(historical_wrong))

    def test_fixed_cardinality_assignment_and_reference_corruptions(self):
        changes = [
            lambda d: d["cases"][1].__setitem__("slot", "anchor_01"),
            lambda d: d["cases"][1].__setitem__("slot", "anchor_02"),
            lambda d: d["cases"].reverse(),
            lambda d: d["design_entries"].reverse(),
            lambda d: d["design_entries"][1].__setitem__("slot", "anchor_01"),
            lambda d: d["design_entries"][0].__setitem__("role", "MUTATION"),
            lambda d: d["design_entries"][0].__setitem__("category", "unsupported_temporal"),
            lambda d: d["design_entries"][0].__setitem__("seed_kind", "uncertain"),
            lambda d: d["design_entries"][1].__setitem__("role", "ANCHOR"),
            lambda d: d["relations"].reverse(),
            lambda d: d["relations"][1].__setitem__("id", "invariant_1"),
            lambda d: d["relations"][0].__setitem__("family", "negation"),
            lambda d: d["relations"][0].__setitem__("mode", "SENSITIVE"),
            lambda d: d["relations"][0].__setitem__("left_slot", "invariant_1"),
            lambda d: d["relations"][0].__setitem__("right_slot", "anchor_01"),
            lambda d: d["relations"][0].__setitem__("right_slot", "anchor_02"),
            lambda d: d["design_entries"][0]["contrast_anchors"][0].__setitem__("text", "absent"),
            lambda d: d["cases"][0].__setitem__("claim", "token-anchor_01 token-anchor_01"),
            lambda d: d["relations"][0]["anchor_map"][0]["right"].__setitem__("text", "absent"),
            lambda d: d["relations"][0]["changed_ranges"].append(
                {"surface": "CORE", "before": "", "after": ""}),
            lambda d: d["relations"][0]["changed_ranges"].append(
                {"surface": "BODY", "before": "absent", "after": "body-token"}),
        ]
        for number, mutate in enumerate(changes):
            with self.subTest(mutation=number), self.assertRaises(ValueError):
                draft = token_draft(self.group, self.inventory)
                mutate(draft)
                self.materialize(draft)

    def test_variant_seed_is_not_invented_and_unicode_offsets_are_codepoints(self):
        for seed in ("positive", "explicit", "uncertain"):
            draft = token_draft(self.group, self.inventory)
            draft["design_entries"][1]["seed_kind"] = seed
            self.materialize(draft)
        draft["cases"][0]["claim"] = "λ 🧬 token-anchor_01"
        result = self.materialize(draft)
        self.assertEqual(result["design_entries"][0]["contrast_anchors"][0],
                         {"text": "token-anchor_01", "start": 4, "end": 19})
        case = result["cases"][0]
        self.assertEqual(case["claim_sha256"], once.sha("λ 🧬 token-anchor_01".encode()))
        self.assertNotIn("slot", case)
        self.assertNotIn("category", case)

    def test_complete_synthetic_corpus_order_and_purity(self):
        drafts = {g["id"]: token_draft(g, self.inventory) for g in self.partition["partitions"]}
        outputs = boundary.assemble(drafts, self.inventory, self.partition, self.schemas)
        cases = [once.decoded(line) for line in outputs["cases.jsonl"].splitlines()]
        design = once.decoded(outputs["design.json"])
        relations = once.decoded(outputs["relations.json"])
        self.assertEqual([c["case_id"] for c in cases], [self.partition["identities"][s]["case_id"]
                                                        for s in self.partition["corpus_order"]])
        self.assertEqual([e["slot"] for e in design["entries"]], self.partition["corpus_order"])
        recipe_order = self.inventory["invariance"] + self.inventory["mutations"]
        self.assertEqual([r["id"] for r in relations["relations"]],
                         [r["slot"] for r in recipe_order])
        self.assertEqual(boundary.assemble(drafts, self.inventory, self.partition, self.schemas),
                         outputs)
        del drafts["author-28"]
        with self.assertRaisesRegex(ValueError, "incomplete/extra"):
            boundary.assemble(drafts, self.inventory, self.partition, self.schemas)

    def test_complete_corpus_without_declared_guard_coverage_fails(self):
        drafts = {g["id"]: token_draft(g, self.inventory) for g in self.partition["partitions"]}
        for draft in drafts.values():
            for entry in draft["design_entries"]:
                entry["guard_opportunities"] = []
        with self.assertRaisesRegex(ValueError, "missing declared guard"):
            boundary.assemble(drafts, self.inventory, self.partition, self.schemas)


class Wrapper(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        manifest = boundary.read(ROOT / boundary.INHERITED_FREEZE)
        files = set(manifest["artifacts"]) | {str(p) for p in
            (boundary.INHERITED_FREEZE, boundary.MODULE, boundary.TESTS, boundary.PROTOCOL)}
        for name in files:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.run = self.root / "research/evidence/semantic-author-slot-bound-v2-unittest"
        self.inventory, self.partition, self.schemas = boundary.authority(self.root)
        self.calls = []
        boundary.prepare(self.root, self.run, CONFIG)

    def fake(self, draft=None, prompt_tokens=100):
        if draft is None:
            draft = copy.deepcopy(boundary.CANARY_OUTPUT)

        def transport(method, endpoint, body=None, timeout=10):
            self.calls.append((method, endpoint, body))
            if endpoint == "/api/version":
                raw = once.encoded({"version": CONFIG["provider_version"]})
            elif endpoint == "/api/tags":
                raw = once.encoded({"models": [{"name": CONFIG["model"],
                                               "digest": CONFIG["model_digest"]}]})
            else:
                raw = once.encoded({"model": CONFIG["model"], "done": True,
                                    "done_reason": "stop", "prompt_eval_count": prompt_tokens,
                                    "response": once.encoded(draft).decode("utf-8")})
            return 200, [("Content-Type", "application/json")], raw, None

        return transport

    def canary(self):
        self.assertEqual(boundary.execute(self.root, self.run, "canary", self.fake())["status"],
                         "PASS_NONSEMANTIC_CANARY_ONLY")

    def test_preparation_and_tampered_freeze_make_zero_transport_calls(self):
        boundary.verify_prepared(self.root, self.run)
        self.assertEqual(self.calls, [])
        path = self.run / "requests/author-01.spec.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "apparatus drift"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])
        self.assertFalse((self.run / "calls").exists())

    def test_removed_freeze_entry_and_aperture_expansion_fail_before_network(self):
        path = self.run / "EXECUTION-FREEZE.json"
        freeze = boundary.read(path)
        freeze["artifacts"].pop(str(boundary.MODULE))
        path.write_bytes(once.encoded(freeze))
        with self.assertRaisesRegex(ValueError, "execution freeze"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])

    def test_executing_source_must_match_frozen_root_before_transport(self):
        module = self.root / boundary.MODULE
        module.write_bytes(module.read_bytes() + b"\n# changed source\n")
        with self.assertRaisesRegex(ValueError, "executing source differs"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])

    def test_old_namespace_and_out_of_order_execution_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "namespace"):
            boundary.execute(self.root, self.root / boundary.PREDECESSOR, "canary", self.fake())
        with self.assertRaisesRegex(ValueError, "prior calls"):
            boundary.execute(self.root, self.run, "author-01", self.fake())
        self.assertEqual(self.calls, [])

    def test_symlinked_output_tree_cannot_escape_new_namespace(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.run / "calls").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "unsafe successor member"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])
        self.assertEqual(list(outside.iterdir()), [])

    def test_incomplete_corpus_attempt_is_preserved_and_never_written_or_retried(self):
        result = boundary.freeze_corpus(self.root, self.run)
        self.assertEqual(result["status"], "APPARATUS_INVALID")
        self.assertIsNone(result["corpus_sha256"])
        self.assertEqual(boundary.read(self.run / "CORPUS-FREEZE-RESULT.json"), result)
        self.assertFalse((self.run / "corpus").exists())
        with self.assertRaises(FileExistsError):
            boundary.freeze_corpus(self.root, self.run)
        with self.assertRaisesRegex(ValueError, "sequence is closed"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])

    def test_canary_requires_observed_input_budget_and_stops_sequence(self):
        result = boundary.execute(self.root, self.run, "canary", self.fake(prompt_tokens=1000000))
        self.assertEqual(result["status"], "APPARATUS_INVALID")
        self.assertEqual(len(self.calls), 3)
        with self.assertRaisesRegex(ValueError, "previous call is invalid"):
            boundary.execute(self.root, self.run, "author-01", self.fake())
        self.assertEqual(len(self.calls), 3)

    def test_invalid_author_response_preserves_raw_and_stops_without_retry(self):
        self.canary()
        draft = token_draft(self.partition["partitions"][0], self.inventory)
        draft["cases"][1]["slot"] = "anchor_02"
        result = boundary.execute(self.root, self.run, "author-01", self.fake(draft))
        self.assertEqual(result["status"], "APPARATUS_INVALID")
        self.assertTrue((self.run / "calls/author-01/provider-response.raw.json").exists())
        self.assertFalse((self.run / "calls/author-01/materialized.json").exists())
        count = len(self.calls)
        for group in ("author-01", "author-02"):
            with self.subTest(group=group), self.assertRaises(ValueError):
                boundary.execute(self.root, self.run, group, self.fake(draft))
        self.assertEqual(len(self.calls), count)
        self.assertFalse((self.run / "corpus").exists())

    def test_schema_pass_cannot_bypass_mechanical_reference_validation(self):
        self.canary()
        draft = token_draft(self.partition["partitions"][0], self.inventory)
        draft["design_entries"][0]["contrast_anchors"] = [{"text": "absent"}]
        result = boundary.execute(self.root, self.run, "author-01", self.fake(draft))
        self.assertEqual(boundary.read(self.run / "calls/author-01/receipt.json")["status"],
                         "PASS_REQUEST_PATH_ONLY")
        self.assertEqual(result["status"], "APPARATUS_INVALID")
        self.assertFalse((self.run / "calls/author-01/materialized.json").exists())

    def test_raw_tampering_blocks_next_request(self):
        self.canary()
        raw = self.run / "calls/canary/provider-response.raw.json"
        raw.write_bytes(raw.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "response custody drift"):
            boundary.execute(self.root, self.run, "author-01", self.fake())
        self.assertEqual(len(self.calls), 3)

    def test_retained_text_discovery_markers_runtime_and_stage_are_revalidated(self):
        self.canary()
        output = self.run / "calls/canary"
        originals = {path.name: path.read_bytes() for path in output.iterdir()}

        def edit(name, key, value):
            data = boundary.read(output / name)
            data[key] = value
            (output / name).write_bytes(once.encoded(data) + b"\n")

        mutations = [
            lambda: (output / "response-text.txt").write_text("ALTERED TEXT"),
            lambda: (output / "provider-discovery.raw.json").unlink(),
            lambda: (output / "models-discovery.raw.json").unlink(),
            lambda: edit("provider-discovery.raw.json", "version", "different-version"),
            lambda: edit("models-discovery.raw.json", "models", []),
            lambda: (output / "before-send.json").unlink(),
            lambda: (output / "send-started.json").unlink(),
            lambda: edit("send-started.json", "request_sha256", "b" * 64),
            lambda: edit("before-send.json", "generation_attempts", 1),
            lambda: edit("receipt.json", "model_digest", "b" * 64),
            lambda: edit("receipt.json", "provider_version", "different-version"),
            lambda: edit("receipt.json", "parameters", {"temperature": 1}),
            lambda: edit("author-boundary.json", "request", "author-28"),
            lambda: edit("author-boundary.json", "stage", "ADJUDICATION"),
            lambda: edit("author-boundary.json", "schema_version", "unknown"),
            lambda: edit("author-boundary.json", "errors", ["undeclared failure"]),
            lambda: edit("author-boundary.json", "adjudication", "FALSE_CLAIM"),
            lambda: edit("author-boundary.json", "semantic_validity", "QUALIFIED"),
            lambda: edit("author-boundary.json", "observed_prompt_tokens", 1),
            lambda: edit("http-response.json", "headers", [["Altered", "retained bytes"]]),
        ]
        spec = boundary.read(self.run / "canary.spec.json")
        for number, mutate in enumerate(mutations):
            for name, raw in originals.items():
                (output / name).write_bytes(raw)
            with self.subTest(mutation=number):
                mutate()
                with self.assertRaises((ValueError, FileNotFoundError)):
                    boundary.checked_call(self.run, "canary", spec, CONFIG,
                                          "PASS_NONSEMANTIC_CANARY_ONLY")
        # Exercise the real next-request entrypoint too, with the final corruption retained.
        group = self.partition["partitions"][0]
        with self.assertRaises(ValueError):
            boundary.execute(self.root, self.run, group["id"],
                             self.fake(token_draft(group, self.inventory)))
        self.assertEqual(len(self.calls), 3)

    def test_consistent_discovery_hashes_cannot_replace_frozen_runtime_identity(self):
        self.canary()
        output = self.run / "calls/canary"
        discovery = boundary.read(output / "models-discovery.raw.json")
        discovery["models"][0]["digest"] = "b" * 64
        (output / "models-discovery.raw.json").write_bytes(once.encoded(discovery) + b"\n")
        receipt = boundary.read(output / "receipt.json")
        receipt["models_discovery_sha256"] = once.sha(
            (output / "models-discovery.raw.json").read_bytes())
        (output / "receipt.json").write_bytes(once.encoded(receipt) + b"\n")
        acceptance = boundary.read(output / "author-boundary.json")
        acceptance["request_receipt_sha256"] = once.sha((output / "receipt.json").read_bytes())
        for name in ("models-discovery.raw.json", "receipt.json"):
            acceptance["transport_artifacts_sha256"][name] = once.sha((output / name).read_bytes())
        (output / "author-boundary.json").write_bytes(once.encoded(acceptance) + b"\n")
        group = self.partition["partitions"][0]
        with self.assertRaisesRegex(ValueError, "discovered runtime mismatch"):
            boundary.execute(self.root, self.run, group["id"],
                             self.fake(token_draft(group, self.inventory)))
        self.assertEqual(len(self.calls), 3)

    def test_self_consistent_materialized_edit_cannot_override_unchanged_raw_response(self):
        self.canary()
        first = self.partition["partitions"][0]
        draft = token_draft(first, self.inventory)
        boundary.execute(self.root, self.run, first["id"], self.fake(draft))
        boundary.checked_materialization(self.run, first, draft, self.inventory,
                                         self.partition, self.schemas)
        path = self.run / "calls/author-01/materialized.json"
        changed = boundary.read(path)
        changed["cases"][0]["claim"] = "CHANGED STRUCTURAL TOKEN"
        path.write_bytes(once.encoded(changed) + b"\n")
        acceptance_path = self.run / "calls/author-01/author-boundary.json"
        acceptance = boundary.read(acceptance_path)
        acceptance["materialized_sha256"] = once.sha(path.read_bytes())
        acceptance_path.write_bytes(once.encoded(acceptance) + b"\n")
        count = len(self.calls)
        second = self.partition["partitions"][1]
        with self.assertRaisesRegex(ValueError, "canonical raw-response rederivation"):
            boundary.execute(self.root, self.run, second["id"],
                             self.fake(token_draft(second, self.inventory)))
        self.assertEqual(len(self.calls), count)
        self.assertFalse((self.run / "calls/author-02").exists())

    def test_all_28_synthetic_partitions_freeze_only_after_exact_raw_revalidation(self):
        self.canary()
        for group in self.partition["partitions"]:
            result = boundary.execute(self.root, self.run, group["id"],
                                      self.fake(token_draft(group, self.inventory)))
            self.assertEqual(result["status"], boundary.STATUS)
        result = boundary.freeze_corpus(self.root, self.run)
        self.assertEqual(result["status"], "PASS_COMPLETE_CORPUS_STRUCTURE_ONLY")
        self.assertEqual(result["adjudication"], "NOT_RUN")
        self.assertEqual(result["semantic_validity"], "NOT_ASSESSED")
        self.assertEqual(set(result["source_acceptance_receipts"]),
                         {"canary", *[g["id"] for g in self.partition["partitions"]]})
        self.assertEqual(len([call for call in self.calls if call[0] == "POST"]), 29)
        for name, digest in result["artifacts"].items():
            self.assertEqual(once.sha((self.run / "corpus" / name).read_bytes()), digest)
        with self.assertRaises(FileExistsError):
            boundary.freeze_corpus(self.root, self.run)


def spare_relation(partition, inventory):
    """A shape-valid relation row, used only to overfill arrays that must stay empty."""
    group = next(g for g in partition["partitions"] if g["relation_slots"])
    return token_draft(group, inventory)["relations"][0]


def corruptions(draft, group, spare):
    """Corrupt each exact tuple array in every way the author boundary must refuse."""
    out = {}

    def corrupt(label, change):
        copied = copy.deepcopy(draft)
        change(copied)
        out[label] = copied

    for field in ("cases", "design_entries", "relations"):
        if draft[field]:
            corrupt(f"{field}: missing last", lambda d, f=field: d[f].pop())
            corrupt(f"{field}: missing first", lambda d, f=field: d[f].pop(0))
            corrupt(f"{field}: extra duplicate",
                    lambda d, f=field: d[f].append(copy.deepcopy(d[f][-1])))
            corrupt(f"{field}: emptied", lambda d, f=field: d.__setitem__(f, []))
        else:
            corrupt(f"{field}: extra row in exact-empty array",
                    lambda d, f=field: d[f].append(copy.deepcopy(spare)))
        if len(draft[field]) > 1:
            corrupt(f"{field}: reordered", lambda d, f=field: d[f].insert(0, d[f].pop(1)))
    other = "anchor_02" if group["anchor_slot"] == "anchor_01" else "anchor_01"
    category = draft["design_entries"][0]["category"]
    other_category = "unsupported_temporal" if category == "full_body_support" \
        else "full_body_support"
    corrupt("cases: wrong slot const", lambda d: d["cases"][0].__setitem__("slot", other))
    corrupt("design_entries: wrong slot const",
            lambda d: d["design_entries"][0].__setitem__("slot", other))
    corrupt("design_entries: wrong role const",
            lambda d: d["design_entries"][0].__setitem__("role", "MUTATION"))
    corrupt("design_entries: wrong category const",
            lambda d: d["design_entries"][0].__setitem__("category", other_category))
    if draft["relations"]:
        row = draft["relations"][0]
        other_family = "exact_duplicate" if row["family"] != "exact_duplicate" else "entity_rename"
        other_mode = "SENSITIVE" if row["mode"] == "INVARIANT" else "INVARIANT"
        corrupt("relations: wrong id const", lambda d: d["relations"][0].__setitem__("id", other))
        corrupt("relations: wrong family const",
                lambda d: d["relations"][0].__setitem__("family", other_family))
        corrupt("relations: wrong mode const",
                lambda d: d["relations"][0].__setitem__("mode", other_mode))
        corrupt("relations: wrong left endpoint",
                lambda d: d["relations"][0].__setitem__("left_slot", row["right_slot"]))
        corrupt("relations: wrong right endpoint",
                lambda d: d["relations"][0].__setitem__("right_slot", other))
    return out


class ProviderSchemaGate(unittest.TestCase):
    POSITIONS = {
        "items false": ({"type": "array", "items": False}, "#/items"),
        "items true": ({"type": "array", "items": True}, "#/items"),
        "items as list": ({"type": "array", "items": [{"type": "string"}]}, "#/items"),
        "prefixItems member": ({"prefixItems": [{"type": "string"}, False]}, "#/prefixItems/1"),
        "property": ({"properties": {"a": True}}, "#/properties/a"),
        "property named like a keyword": ({"properties": {"uniqueItems": False}},
                                          "#/properties/uniqueItems"),
        "$defs member": ({"$defs": {"a": True}}, "#/$defs/a"),
        "allOf member": ({"allOf": [True]}, "#/allOf/0"),
        "anyOf member": ({"anyOf": [{"type": "null"}, False]}, "#/anyOf/1"),
        "oneOf member": ({"oneOf": [True]}, "#/oneOf/0"),
        "not": ({"not": True}, "#/not"),
        "if": ({"if": True}, "#/if"),
        "then": ({"then": False}, "#/then"),
        "else": ({"else": True}, "#/else"),
        "contains": ({"contains": True}, "#/contains"),
        "propertyNames": ({"propertyNames": True}, "#/propertyNames"),
        "additionalItems": ({"additionalItems": False}, "#/additionalItems"),
        "unevaluatedItems": ({"unevaluatedItems": False}, "#/unevaluatedItems"),
        "unevaluatedProperties": ({"unevaluatedProperties": False}, "#/unevaluatedProperties"),
        "patternProperties": ({"patternProperties": {"^a": True}}, "#/patternProperties/^a"),
        "dependentSchemas": ({"dependentSchemas": {"a": True}}, "#/dependentSchemas/a"),
        "additionalProperties true": ({"additionalProperties": True}, "#/additionalProperties"),
        "additionalProperties zero is not false": ({"additionalProperties": 0},
                                                   "#/additionalProperties"),
        "unclassified boolean keyword": ({"nullable": True}, "#/nullable"),
        "deeply nested": ({"$defs": {"x": {"properties": {"y": {"items": {"allOf": [
            {"anyOf": [{}, False]}]}}}}}}, "#/$defs/x/properties/y/items/allOf/0/anyOf/1"),
    }

    def test_boolean_or_nonobject_is_rejected_in_every_schema_position(self):
        for label, (schema, pointer) in self.POSITIONS.items():
            with self.subTest(position=label):
                self.assertEqual(boundary.boolean_subschemas(schema), [pointer])
                with self.assertRaisesRegex(ValueError, "boolean subschema"):
                    boundary.provider_schema_gate(schema, "fixture")

    def test_every_offending_position_is_reported_not_only_the_first(self):
        schema = {"properties": {"a": {"items": False}, "b": {"allOf": [True, {"not": False}]}}}
        self.assertEqual(boundary.boolean_subschemas(schema),
                         ["#/properties/a/items", "#/properties/b/allOf/0",
                          "#/properties/b/allOf/1/not"])

    def test_root_boolean_schema_is_rejected(self):
        for root in (True, False):
            self.assertEqual(boundary.boolean_subschemas(root), ["#"])

    def test_declared_flags_and_data_values_are_not_subschemas(self):
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "properties": {
                "items": {"type": "array", "uniqueItems": True, "items": {"type": "string"}},
                "enum": {"enum": [True, False, None]},
                "const": {"const": False},
                "flag": {"type": "boolean", "default": False, "examples": [True, False]},
            },
            "required": ["items", "enum", "const", "flag"], "additionalProperties": False}
        self.assertEqual(boundary.boolean_subschemas(schema), [])
        self.assertEqual(boundary.provider_schema_gate(schema, "fixture")["boolean_subschemas"], 0)

    def test_schema_keywords_exclude_property_names_and_data(self):
        schema = {"type": "object", "properties": {"items": {"const": True}, "type": {
            "enum": [1]}}, "additionalProperties": False}
        self.assertEqual(boundary.schema_keywords(schema),
                         {"type", "properties", "additionalProperties", "const", "enum"})

    def test_gate_message_names_the_provider_failure_location(self):
        closed = reference.tuple_schema("rows", [{"slot": "token-a"}])
        schema = {"type": "object", "properties": {"rows": closed}}
        with self.assertRaisesRegex(ValueError, "#/properties/rows/items"):
            boundary.provider_schema_gate(schema, "canary")


class ProviderFacingSchemas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory, cls.partition, cls.schemas = boundary.authority(ROOT)
        cls.groups = cls.partition["partitions"]
        cls.specs = boundary.request_specs(ROOT, cls.inventory, cls.partition, cls.schemas)
        cls.spare = spare_relation(cls.partition, cls.inventory)

    def schema(self, group):
        return self.specs[group["id"]]["output_schema"]

    def errors(self, group, draft):
        return list(Draft202012Validator(self.schema(group)).iter_errors(draft))

    def validators(self, errors):
        return {error.validator for error in errors}

    def test_all_28_generated_author_schemas_have_no_boolean_subschemas(self):
        self.assertEqual(len(self.specs), 28)
        for key, spec in self.specs.items():
            with self.subTest(request=key):
                self.assertEqual(boundary.boolean_subschemas(spec["output_schema"]), [])

    def test_the_gate_detects_the_real_v1_construct_in_every_v1_author_schema(self):
        expected = [f"#/properties/{name}/items" for name in ("cases", "design_entries",
                                                               "relations")]
        for group in self.groups:
            old = reference.bound_schema(group, self.inventory, self.schemas)
            with self.subTest(request=group["id"]):
                self.assertEqual(sorted(boundary.boolean_subschemas(old)), sorted(expected))

    def test_v2_schema_is_the_v1_schema_minus_only_its_closed_tuple_booleans(self):
        for group in self.groups:
            old = reference.bound_schema(group, self.inventory, self.schemas)
            for tuple_schema in old["properties"].values():
                self.assertIs(tuple_schema.pop("items"), False)
            with self.subTest(request=group["id"]):
                self.assertEqual(old, self.schema(group))

    def test_assignments_instructions_and_aperture_are_unchanged_from_v1(self):
        old = reference.request_specs(ROOT, self.inventory, self.partition, self.schemas)
        self.assertEqual(boundary.BOUND_INSTRUCTION, reference.BOUND_INSTRUCTION)
        self.assertEqual(set(old), set(self.specs))
        for key, spec in self.specs.items():
            with self.subTest(request=key):
                for field in ("role_instruction", "artifacts", "data"):
                    self.assertEqual(spec[field], old[key][field])

    def test_exact_cardinality_closes_every_tuple_without_an_items_keyword(self):
        for group in self.groups:
            counts = {"cases": len(group["slots"]), "design_entries": len(group["slots"]),
                      "relations": len(group["relation_slots"])}
            for name, tuple_schema in self.schema(group)["properties"].items():
                with self.subTest(request=group["id"], field=name):
                    count = counts[name]
                    self.assertEqual((tuple_schema["minItems"], tuple_schema["maxItems"]),
                                     (count, count))
                    self.assertNotIn("items", tuple_schema)
                    self.assertEqual(len(tuple_schema.get("prefixItems", [])), count)

    def test_missing_item_is_rejected(self):
        group = self.groups[0]
        for field in ("cases", "design_entries", "relations"):
            draft = token_draft(group, self.inventory)
            draft[field].pop()
            with self.subTest(field=field):
                self.assertIn("minItems", self.validators(self.errors(group, draft)))

    def test_extra_item_is_rejected_by_exact_cardinality(self):
        group = self.groups[0]
        for field in ("cases", "design_entries", "relations"):
            draft = token_draft(group, self.inventory)
            draft[field].append(copy.deepcopy(draft[field][-1]))
            with self.subTest(field=field):
                self.assertNotIn("items", self.schema(group)["properties"][field])
                self.assertIn("maxItems", self.validators(self.errors(group, draft)))

    def test_reordered_and_wrong_positional_slots_are_rejected(self):
        group = self.groups[0]
        for field in ("cases", "design_entries", "relations"):
            draft = token_draft(group, self.inventory)
            draft[field].insert(0, draft[field].pop(1))
            with self.subTest(field=field):
                self.assertIn("const", self.validators(self.errors(group, draft)))

    def test_wrong_const_assignment_is_rejected(self):
        group = self.groups[0]
        draft = token_draft(group, self.inventory)
        for label in ("cases: wrong slot const", "design_entries: wrong role const",
                      "design_entries: wrong category const", "relations: wrong id const",
                      "relations: wrong family const", "relations: wrong mode const",
                      "relations: wrong left endpoint", "relations: wrong right endpoint"):
            bad = corruptions(draft, group, self.spare)[label]
            with self.subTest(corruption=label):
                self.assertIn("const", self.validators(self.errors(group, bad)))

    def test_empty_arrays_remain_exactly_empty(self):
        empty = [g for g in self.groups if not g["relation_slots"]]
        self.assertGreaterEqual(len(empty), 12)
        for group in empty:
            draft = token_draft(group, self.inventory)
            with self.subTest(request=group["id"]):
                self.assertEqual(self.schema(group)["properties"]["relations"],
                                 {"type": "array", "minItems": 0, "maxItems": 0})
                self.assertEqual(draft["relations"], [])
                self.assertEqual(self.errors(group, draft), [])
                draft["relations"].append(copy.deepcopy(self.spare))
                self.assertIn("maxItems", self.validators(self.errors(group, draft)))

    def test_every_corruption_is_rejected_by_v2_and_by_v1_alike(self):
        for group in self.groups:
            old = Draft202012Validator(reference.bound_schema(group, self.inventory,
                                                              self.schemas))
            new = Draft202012Validator(self.schema(group))
            draft = token_draft(group, self.inventory)
            self.assertTrue(old.is_valid(draft) and new.is_valid(draft), group["id"])
            for entry in draft["design_entries"][1:]:
                for seed in ("positive", "explicit", "uncertain"):
                    entry["seed_kind"] = seed
                    self.assertTrue(old.is_valid(draft) and new.is_valid(draft), group["id"])
            draft = token_draft(group, self.inventory)
            for label, bad in corruptions(draft, group, self.spare).items():
                with self.subTest(request=group["id"], corruption=label):
                    self.assertEqual((old.is_valid(bad), new.is_valid(bad)), (False, False))

    def test_provider_facing_schemas_still_pass_the_acceptance_validator(self):
        for group in self.groups:
            draft = token_draft(group, self.inventory)
            with self.subTest(request=group["id"]):
                frozen.schema_check(draft, self.schema(group))
                self.assertTrue(boundary.validate_draft(draft, group, self.inventory,
                                                        self.partition, self.schemas))


class CanaryFeatureCoverage(unittest.TestCase):
    AUTHORING_KEYWORDS = {
        "$defs", "$ref", "$schema", "additionalProperties", "allOf", "anyOf", "const", "enum",
        "items", "maxItems", "minItems", "minLength", "prefixItems", "properties", "required",
        "title", "type", "uniqueItems"}

    @classmethod
    def setUpClass(cls):
        cls.inventory, cls.partition, cls.schemas = boundary.authority(ROOT)
        cls.specs = boundary.request_specs(ROOT, cls.inventory, cls.partition, cls.schemas)
        cls.canary = boundary.canary_spec(cls.specs, CONFIG)
        cls.validator = Draft202012Validator(cls.canary["output_schema"])

    def test_canary_exercises_exactly_the_keywords_the_author_schemas_use(self):
        author = set()
        for spec in self.specs.values():
            author |= boundary.schema_keywords(spec["output_schema"])
        self.assertEqual(author, self.AUTHORING_KEYWORDS)
        self.assertEqual(boundary.schema_keywords(self.canary["output_schema"]),
                         self.AUTHORING_KEYWORDS)

    def test_the_v1_canary_exercised_only_twelve_of_the_eighteen(self):
        old_specs = reference.request_specs(ROOT, self.inventory, self.partition, self.schemas)
        old = reference.canary_spec(old_specs, CONFIG)
        used = boundary.schema_keywords(old["output_schema"])
        self.assertEqual(self.AUTHORING_KEYWORDS - used,
                         {"$schema", "anyOf", "enum", "minLength", "title", "uniqueItems"})
        self.assertEqual(len(used), 12)

    def test_the_declared_output_is_valid_and_every_feature_is_an_active_constraint(self):
        self.assertEqual(list(self.validator.iter_errors(boundary.CANARY_OUTPUT)), [])
        seen = set()

        def reject(change):
            bad = copy.deepcopy(boundary.CANARY_OUTPUT)
            change(bad)
            errors = list(self.validator.iter_errors(bad))
            self.assertTrue(errors)
            seen.update(error.validator for error in errors)

        reject(lambda d: d["rows"].pop())
        reject(lambda d: d["rows"].append(copy.deepcopy(d["rows"][0])))
        reject(lambda d: d["rows"].reverse())
        reject(lambda d: d["rows"][0].__setitem__("kind", "BOGUS"))
        reject(lambda d: d["rows"][0].__setitem__("label", ""))
        reject(lambda d: d["rows"][0].__setitem__("tags", ["t", "t"]))
        reject(lambda d: d["rows"][0].__setitem__("tags", ["a", "b", "c", "d"]))
        reject(lambda d: d["rows"][0].__setitem__("note", 5))
        reject(lambda d: d["rows"][0].__setitem__("extra", 1))
        reject(lambda d: d["rows"][0].pop("tags"))
        reject(lambda d: d["rows"][0].__setitem__("spans", {}))
        reject(lambda d: d["none"].append({}))
        reject(lambda d: d.__setitem__("extra", 1))
        self.assertGreaterEqual(seen, {
            "minItems", "maxItems", "const", "enum", "minLength", "uniqueItems", "anyOf",
            "additionalProperties", "required", "type"})

    def test_the_canary_uses_the_authoring_tuple_construct_and_property_overlap(self):
        schema = self.canary["output_schema"]
        positions = [{"slot": "token-a", "kind": "PROBE"}, {"slot": "token-b", "kind": "CONTROL"}]
        self.assertEqual(schema["properties"]["rows"], boundary.tuple_schema("rows", positions))
        self.assertEqual(schema["properties"]["none"],
                         {"type": "array", "minItems": 0, "maxItems": 0})
        defined = set(schema["$defs"]["rows"]["properties"])
        for position in schema["properties"]["rows"]["prefixItems"]:
            self.assertEqual(position["allOf"][0], {"$ref": "#/$defs/rows"})
            self.assertTrue(set(position["allOf"][1]["properties"]) <= defined)
        self.assertEqual(schema["$defs"]["rows"]["properties"]["kind"]["enum"],
                         ["PROBE", "CONTROL", "OTHER"])

    def test_the_canary_still_embeds_the_largest_author_prompt_as_uninterpreted_data(self):
        prompts = {key: once.build_request(spec, CONFIG)[1] for key, spec in self.specs.items()}
        largest = max(prompts, key=lambda key: len(prompts[key]))
        self.assertEqual(self.canary["data"], {"probe_from_request": largest,
                                               "uninterpreted_probe": prompts[largest].decode()})
        self.assertEqual(self.canary["artifacts"], [])
        self.assertEqual(once.decoded(boundary.CANARY_TEXT), boundary.CANARY_OUTPUT)
        self.assertIn(boundary.CANARY_TEXT, self.canary["role_instruction"])


class ProviderGateWiring(unittest.TestCase):
    setUp = Wrapper.setUp
    fake = Wrapper.fake
    canary = Wrapper.canary

    def test_construction_refuses_a_closed_tuple_with_boolean_items(self):
        group = self.partition["partitions"][0]
        specs = boundary.request_specs(self.root, self.inventory, self.partition, self.schemas)
        with mock.patch.object(boundary, "tuple_schema", reference.tuple_schema):
            with self.assertRaisesRegex(ValueError, "boolean subschema"):
                boundary.bound_schema(group, self.inventory, self.schemas)
            with self.assertRaisesRegex(ValueError, "boolean subschema"):
                boundary.request_specs(self.root, self.inventory, self.partition, self.schemas)
            with self.assertRaisesRegex(ValueError, "canary schema"):
                boundary.canary_spec(specs, CONFIG)

    def test_prepare_refuses_before_any_run_directory_exists(self):
        fresh = self.root / "research/evidence/semantic-author-slot-bound-v2-refused"
        with mock.patch.object(boundary, "tuple_schema", reference.tuple_schema):
            with self.assertRaisesRegex(ValueError, "boolean subschema"):
                boundary.prepare(self.root, fresh, CONFIG)
        self.assertFalse(fresh.exists())
        self.assertEqual(self.calls, [])

    def test_presend_check_gates_the_exact_request_format_and_the_frozen_bytes(self):
        spec = boundary.read(self.run / "canary.spec.json")
        boundary.presend_check(self.run, "canary", spec, CONFIG)
        closed = copy.deepcopy(spec)
        closed["output_schema"]["properties"]["rows"]["items"] = False
        # The inherited request builder accepts it: boolean subschemas are valid Draft 2020-12.
        once.build_request(closed, CONFIG)
        with self.assertRaisesRegex(ValueError, "#/properties/rows/items"):
            boundary.presend_check(self.run, "canary", closed, CONFIG)
        frozen_request = self.run / "generated/canary.request.json"
        frozen_request.write_bytes(frozen_request.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "frozen request"):
            boundary.presend_check(self.run, "canary", spec, CONFIG)

    def test_execute_runs_the_presend_check_before_any_network_action(self):
        with mock.patch.object(boundary, "presend_check",
                               side_effect=ValueError("boolean subschema")):
            with self.assertRaisesRegex(ValueError, "boolean subschema"):
                boundary.execute(self.root, self.run, "canary", self.fake())
        self.assertEqual(self.calls, [])
        self.assertFalse((self.run / "calls").exists())

    def test_exact_provider_requests_are_frozen_before_any_call(self):
        freeze = boundary.read(self.run / "EXECUTION-FREEZE.json")
        plan = boundary.read(self.run / "PLAN.json")
        specs = boundary.request_specs(self.root, self.inventory, self.partition, self.schemas)
        calls = {**specs, "canary": boundary.read(self.run / "canary.spec.json")}
        self.assertEqual(set(plan["request_sha256"]), set(calls))
        for key, spec in calls.items():
            request, prompt = once.build_request(spec, CONFIG)
            for name, raw in ((f"{key}.request.json", request), (f"{key}.prompt.txt", prompt)):
                path = self.run / "generated" / name
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(freeze["artifacts"][str(path.relative_to(self.root))],
                                 once.sha(raw))
            self.assertEqual(plan["request_sha256"][key], once.sha(request))
        self.assertEqual(self.calls, [])

    def test_missing_extra_or_altered_generated_files_fail_before_network(self):
        generated = self.run / "generated"
        victim = generated / "author-01.request.json"
        original = victim.read_bytes()
        victim.write_bytes(original + b" ")
        with self.assertRaisesRegex(ValueError, "apparatus drift"):
            boundary.execute(self.root, self.run, "canary", self.fake())
        victim.write_bytes(original)
        victim.unlink()
        with self.assertRaises((ValueError, FileNotFoundError)):
            boundary.execute(self.root, self.run, "canary", self.fake())
        victim.write_bytes(original)
        (generated / "unfrozen.request.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "incomplete/extra execution freeze"):
            boundary.verify_prepared(self.root, self.run)
        self.assertEqual(self.calls, [])

    def test_plan_records_the_gate_and_predecessor_and_is_rederived_on_verify(self):
        path = self.run / "PLAN.json"
        plan = boundary.read(path)
        self.assertEqual(plan["schema_version"], "semantic-author-bound-plan/v2")
        gate = plan["provider_schema_gate"]
        self.assertEqual((gate["status"], gate["schemas_checked"], gate["boolean_subschemas"]),
                         ("PASS_NO_BOOLEAN_SUBSCHEMAS", 29, 0))
        self.assertEqual(plan["predecessor"], {
            "run": "semantic-author-slot-bound-v1-20261004-attempt01",
            "module_sha256": "74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450",
            "status": "APPARATUS_INVALID"})
        plan["provider_schema_gate"]["boolean_subschemas"] = 1
        path.write_bytes(once.encoded(plan) + b"\n")
        freeze_path = self.run / "EXECUTION-FREEZE.json"
        freeze = boundary.read(freeze_path)
        freeze["artifacts"][str(path.relative_to(self.root))] = once.sha(path.read_bytes())
        freeze_path.write_bytes(once.encoded(freeze) + b"\n")
        with self.assertRaisesRegex(ValueError, "invalid prospective plan"):
            boundary.verify_prepared(self.root, self.run)

    def test_cli_prepare_and_verify_exit_zero_and_report_the_gate(self):
        config = self.root / "runtime-config.input.json"
        config.write_bytes(once.encoded(CONFIG))
        fresh = self.root / "research/evidence/semantic-author-slot-bound-v2-cli"

        def cli(*arguments):
            out = io.StringIO()
            with mock.patch.object(sys, "argv", ["boundary", *arguments]), \
                    contextlib.redirect_stdout(out):
                code = boundary.main()
            return code, once.decoded(out.getvalue())

        code, plan = cli("prepare", "--root", str(self.root), "--run-dir", str(fresh),
                         "--config", str(config))
        self.assertEqual((code, plan["status"]), (0, "NOT_RUN"))
        code, verified = cli("verify", "--root", str(self.root), "--run-dir", str(fresh))
        self.assertEqual(code, 0)
        self.assertEqual(verified, {
            "status": "PASS_PROSPECTIVE_PLAN_ONLY", "partitions": 28, "cases": 44,
            "relations": 16, "provider_schema_gate": "PASS_NO_BOOLEAN_SUBSCHEMAS",
            "provider_calls_in_this_action": 0, "semantic_validity": "NOT_ASSESSED"})
        self.assertEqual(self.calls, [])

    def test_v1_run_directories_are_outside_the_v2_namespace(self):
        old = self.root / "research/evidence/semantic-author-slot-bound-v1-20261004-attempt01"
        with self.assertRaisesRegex(ValueError, "namespace"):
            boundary.run_path(self.root, old)
        with self.assertRaisesRegex(ValueError, "namespace"):
            boundary.execute(self.root, old, "canary", self.fake())
        self.assertEqual(self.calls, [])

    def test_the_declared_canary_output_passes(self):
        self.canary()
        self.assertEqual(boundary.read(self.run / "calls/canary/author-boundary.json")["status"],
                         "PASS_NONSEMANTIC_CANARY_ONLY")

    def test_a_v1_shaped_canary_response_is_not_accepted_by_the_richer_canary(self):
        stale = {"rows": [{"slot": "token-a"}, {"slot": "token-b"}]}
        result = boundary.execute(self.root, self.run, "canary", self.fake(stale))
        self.assertEqual(result["status"], "APPARATUS_INVALID")
        with self.assertRaisesRegex(ValueError, "previous call is invalid"):
            boundary.execute(self.root, self.run, "author-01", self.fake())


if __name__ == "__main__":
    unittest.main()
