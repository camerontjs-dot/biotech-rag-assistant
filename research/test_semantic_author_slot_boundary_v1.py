"""Uninterpreted structural tokens and fake HTTP only; zero semantic/provider evidence."""

from __future__ import annotations

import copy
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import build_semantic_author_requests as predecessor
import check_semantic_assessor_preparation as frozen
import run_semantic_request_once as once
import semantic_author_slot_boundary_v1 as boundary

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
        self.run = self.root / "research/evidence/semantic-author-slot-bound-v1-unittest"
        self.inventory, self.partition, self.schemas = boundary.authority(self.root)
        self.calls = []
        boundary.prepare(self.root, self.run, CONFIG)

    def fake(self, draft=None, prompt_tokens=100):
        if draft is None:
            draft = {"rows": [{"slot": "token-a"}, {"slot": "token-b"}]}

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
        self.assertEqual(len([call for call in self.calls if call[0] == "POST"]), 29)
        for name, digest in result["artifacts"].items():
            self.assertEqual(once.sha((self.run / "corpus" / name).read_bytes()), digest)
        with self.assertRaises(FileExistsError):
            boundary.freeze_corpus(self.root, self.run)


if __name__ == "__main__":
    unittest.main()
