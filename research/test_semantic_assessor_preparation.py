"""Physical structural/custody falsifiers using uninterpreted tokens, not semantic controls."""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

import check_semantic_assessor_preparation as checker

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / checker.PACKAGE


def opaque():
    return str(uuid.uuid4())


def packet():
    text = "BODY_TOKEN"
    return {"case_id": opaque(), "claim": "CLAIM_TOKEN",
            "claim_sha256": checker.sha(b"CLAIM_TOKEN"),
            "authorized_body": [{"witness_id": opaque(), "source_id": opaque(), "text": text,
                                 "text_sha256": checker.sha(text.encode()),
                                 "source_sha256": checker.sha(text.encode()),
                                 "source_span": {"start": 0, "end": len(text)}}],
            "distractors": [], "projection": None}


def annotation(case):
    return {"case_id": case["case_id"], "input_sha256": checker.canonical_sha(case),
            "obligations": [{"id": "opaque-node", "kind": "ASSERTION",
                             "claim_anchors": [{"start": 0, "end": 11, "text": "CLAIM_TOKEN"}],
                             "scope_anchors": [], "parent_id": None, "scope_dependency_ids": [],
                             "meaning": "UNINTERPRETED_SCHEMA_VALUE", "materiality": "UNKNOWN"}],
            "relations": [{"obligation_id": "opaque-node",
                           "witness_ids": [case["authorized_body"][0]["witness_id"]],
                           "relation": "SILENT", "evidence": [],
                           "rationale": "UNINTERPRETED_SCHEMA_VALUE", "alternatives": []}],
            "coverage": "UNKNOWN", "exclusions": [], "uncertainties": ["STRUCTURAL_TOKEN"],
            "decomposition": None}


class StructureTests(unittest.TestCase):
    def setUp(self):
        self.schemas = {name: checker.read_json(PACKAGE / "schemas" / f"{name}.schema.json")
                        for name in checker.SCHEMA_NAMES}
        self.case = packet()
        self.ann = annotation(self.case)

    def test_backend_accepts_only_structural_tokens(self):
        checker.validate_case(self.case, self.schemas["case"])
        checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_no_expected_answer_field_in_packet(self):
        self.case["expected_action"] = "UNINTERPRETED_FORBIDDEN_FIELD"
        with self.assertRaisesRegex(ValueError, "Additional properties"):
            checker.validate_case(self.case, self.schemas["case"])

    def test_body_hash_drift(self):
        self.case["authorized_body"][0]["text"] += "X"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            checker.validate_case(self.case, self.schemas["case"])

    def test_source_span_drift(self):
        self.case["authorized_body"][0]["source_span"]["end"] -= 1
        with self.assertRaisesRegex(ValueError, "source span"):
            checker.validate_case(self.case, self.schemas["case"])

    def test_claim_hash_drift(self):
        self.case["claim"] += "X"
        with self.assertRaisesRegex(ValueError, "claim hash"):
            checker.validate_case(self.case, self.schemas["case"])

    def test_identifier_encodes_category_rejected(self):
        self.case["case_id"] = "FULL_SUPPORT_CASE"
        with self.assertRaises(ValueError):
            checker.validate_case(self.case, self.schemas["case"])

    def test_nonauthoritative_witness_rejected(self):
        other = opaque()
        self.case["distractors"] = [{"id": other, "surface": "HEADING", "text": "TOKEN"}]
        self.ann["input_sha256"] = checker.canonical_sha(self.case)
        self.ann["relations"][0]["witness_ids"] = [other]
        with self.assertRaisesRegex(ValueError, "nonauthoritative"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_missing_atomic_matrix_cell(self):
        extra = copy.deepcopy(self.case["authorized_body"][0])
        extra["witness_id"] = opaque()
        self.case["authorized_body"].append(extra)
        self.ann["input_sha256"] = checker.canonical_sha(self.case)
        with self.assertRaisesRegex(ValueError, "missing atomic"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_unknown_obligation_and_duplicate_row(self):
        invalid = copy.deepcopy(self.ann)
        invalid["relations"][0]["obligation_id"] = "absent"
        with self.assertRaisesRegex(ValueError, "unknown relation obligation"):
            checker.validate_annotation(invalid, self.case, self.schemas["annotation"])
        self.ann["relations"].append(copy.deepcopy(self.ann["relations"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate relation"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_evidence_text_must_match(self):
        row = self.ann["relations"][0]
        row["relation"] = "ENTAILED"
        row["evidence"] = [{"witness_id": row["witness_ids"][0],
                            "start": 0, "end": 4, "text": "LIES"}]
        with self.assertRaisesRegex(ValueError, "anchor text mismatch"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_ambiguous_requires_alternatives(self):
        row = self.ann["relations"][0]
        row["relation"] = "AMBIGUOUS"
        row["evidence"] = [{"witness_id": row["witness_ids"][0],
                            "start": 0, "end": 4, "text": "BODY"}]
        with self.assertRaisesRegex(ValueError, "competing readings"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_complete_cannot_hide_unknown_materiality(self):
        self.ann["coverage"] = "COMPLETE"
        with self.assertRaisesRegex(ValueError, "UNKNOWN materiality"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_projection_cannot_disappear(self):
        self.case["projection"] = {"core_text": "TOKEN", "gap_text": "TOKEN"}
        self.ann["input_sha256"] = checker.canonical_sha(self.case)
        with self.assertRaisesRegex(ValueError, "applicability omitted"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_cyclic_scope_dependency_rejected(self):
        first = self.ann["obligations"][0]
        second = copy.deepcopy(first)
        second.update(id="other-node", kind="TIME", parent_id=first["id"],
                      scope_dependency_ids=[first["id"]])
        first["scope_dependency_ids"] = [second["id"]]
        self.ann["obligations"].append(second)
        with self.assertRaisesRegex(ValueError, "cyclic scope"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_external_schema_cannot_trigger_network_resolution(self):
        with self.assertRaisesRegex(ValueError, "external schema"):
            checker.schema_check({}, {"$ref": "https://invalid.example/forbidden"})

    def test_malformed_schema_is_a_finding(self):
        with self.assertRaisesRegex(ValueError, "invalid schema"):
            checker.schema_check({}, {"type": "not-a-json-type"})

    def test_unicode_offsets_are_codepoints(self):
        self.case["claim"] = "éΩ"
        self.case["claim_sha256"] = checker.sha(self.case["claim"].encode())
        self.ann["input_sha256"] = checker.canonical_sha(self.case)
        self.ann["obligations"][0]["claim_anchors"] = [{"start": 0, "end": 2, "text": "éΩ"}]
        checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])
        self.ann["obligations"][0]["claim_anchors"][0]["end"] = 4
        with self.assertRaisesRegex(ValueError, "anchor range"):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_missing_guard_justification_and_unjudged_guards(self):
        self.case["projection"] = {"core_text": "TOKEN", "gap_text": "TOKEN"}
        self.ann["input_sha256"] = checker.canonical_sha(self.case)
        self.ann["decomposition"] = {
            "applicability": "REQUIRED", "core_ids": [], "gap_ids": [], "body_witness_ids": [],
            "guards": dict.fromkeys(checker.GUARDS, "UNKNOWN"), "guard_justifications": {}}
        with self.assertRaises(ValueError):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])
        self.ann["decomposition"]["applicability"] = "NOT_REQUIRED"
        with self.assertRaises(ValueError):
            checker.validate_annotation(self.ann, self.case, self.schemas["annotation"])

    def test_corpus_slot_and_endpoint_checks_use_tokens_only(self):
        inventory = checker.read_json(PACKAGE / "case-design.json")
        specs = inventory["anchors"] + inventory["invariance"] + inventory["mutations"]
        packets = [packet() for _ in specs]
        entries = []
        for spec, case in zip(specs, packets, strict=True):
            entries.append({
                "slot": spec["slot"], "case_id": case["case_id"],
                "category": spec.get("category", spec.get("anchor_category")),
                "role": ("ANCHOR" if "category" in spec else
                         "INVARIANT" if spec["mode"] == "INVARIANT" else "MUTATION"),
                "seed_kind": spec.get("seed_kind", "explicit"),
                "guard_opportunities": [{"guard": g, "value": v} for g in checker.GUARDS
                                        for v in ("TRUE", "FALSE", "UNKNOWN")],
                "author_hypothesis": "UNINTERPRETED_SCHEMA_VALUE", "contrast_anchors": []})
        ids = {e["slot"]: e["case_id"] for e in entries}
        anchors = {s["category"]: ids[s["slot"]] for s in inventory["anchors"]}
        rows = [{"id": s["slot"], "family": s["family"], "mode": s["mode"],
                 "left_case_id": anchors[s["anchor_category"]], "right_case_id": ids[s["slot"]],
                 "dimensions": ["STRUCTURAL_TOKEN"], "anchor_map": [], "changed_ranges": [],
                 "hypothesis": "UNINTERPRETED_SCHEMA_VALUE"}
                for s in inventory["invariance"] + inventory["mutations"]]
        design = {"corpus_id": inventory["corpus_id"], "entries": entries}
        relations = {"corpus_id": inventory["corpus_id"], "relations": rows}
        checker.validate_corpus(packets, design, relations, self.schemas, inventory)
        relations["relations"][0]["right_case_id"] = opaque()
        with self.assertRaisesRegex(ValueError, "endpoint"):
            checker.validate_corpus(packets, design, relations, self.schemas, inventory)

    def test_strict_json_rejects_duplicate_and_nan(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.json"
            for text in ('{"x":1,"x":2}', '{"x":NaN}'):
                path.write_text(text)
                with self.assertRaises(ValueError):
                    checker.read_json(path)

    def test_missing_backend_is_physically_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            input_path = temporary / "packet.json"
            input_path.write_text(json.dumps(self.case))
            receipt = temporary / "receipt.json"
            result = subprocess.run(
                [sys.executable, "-S",
                 str(ROOT / "research/check_semantic_assessor_preparation.py"),
                 "--root", str(ROOT), "--kind", "case", "--input", str(input_path),
                 "--receipt", str(receipt)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(checker.read_json(receipt)["status"], "CHECK_UNAVAILABLE")

    def test_missing_input_retains_failure_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.json"
            result = subprocess.run(
                [sys.executable, str(ROOT / "research/check_semantic_assessor_preparation.py"),
                 "--root", str(ROOT), "--kind", "case", "--input", str(receipt.parent / "absent"),
                 "--receipt", str(receipt)], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(checker.read_json(receipt)["status"], "CHECK_UNAVAILABLE")

    def test_path_traversal_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            (temporary / "target").write_text("TOKEN")
            (temporary / "link").symlink_to(temporary / "target")
            for reference in ("../target", "link"):
                with self.assertRaises(ValueError):
                    checker.inside(temporary, reference)

    def test_clean_receipt_cannot_hide_forbidden_exposure(self):
        artifact = {"reference": "STRUCTURAL_TOKEN", "sha256": "0" * 64}
        receipt = {
            "stage": "CASE_AUTHOR", "context_id": "TOKEN", "initialization_sha256": "0" * 64,
            "started_at_utc": "TOKEN", "finished_at_utc": "TOKEN",
            "allowed_artifacts": [artifact], "exposed_artifacts": [artifact],
            "forbidden_exposures": [], "output_artifacts": [], "contamination_status": "CLEAN",
            "identity": {"actor_kind": "AGENT", "model_provider": None, "model_version": None,
                         "tools": [], "shared_system_context": "STRUCTURAL_TOKEN"},
            "independence": {k: {"status": "UNKNOWN", "basis": "STRUCTURAL_TOKEN"}
                             for k in ("context", "implementation", "model_tool", "data", "human",
                                       "training_history")},
            "counts": dict.fromkeys(("case_author_launches", "adjudicator_launches",
                                     "adjudicated_cases", "semantic_assessor_calls",
                                     "reducer_calls", "project_generation_calls"), 0),
            "deviations": []}
        checker.validate_receipt(receipt, self.schemas["launch-receipt"])
        receipt["forbidden_exposures"] = [artifact]
        with self.assertRaisesRegex(ValueError, "forbidden exposure"):
            checker.validate_receipt(receipt, self.schemas["launch-receipt"])

    def test_preparation_hash_custody_and_missing_predecessor(self):
        manifest = checker.read_json(PACKAGE / "package-manifest.json")
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            references = set(manifest["artifacts"]) | set(checker.DOWNSTREAM)
            references.add(str(checker.PACKAGE / "package-manifest.json"))
            for reference in references:
                target = temporary / reference
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / reference, target)
            checker.check_preparation(temporary)
            target = temporary / checker.PACKAGE / "rubric.md"
            original = target.read_bytes()
            target.write_bytes(original + b"DRIFT")
            with self.assertRaisesRegex(ValueError, "drift"):
                checker.check_preparation(temporary)
            target.write_bytes(original)
            (temporary / next(iter(checker.DOWNSTREAM))).unlink()
            with self.assertRaisesRegex(ValueError, "missing"):
                checker.check_preparation(temporary)


if __name__ == "__main__":
    unittest.main()
