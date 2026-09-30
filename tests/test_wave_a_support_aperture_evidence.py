"""Offline custody falsifiers; these tests assign no semantic classifications."""

from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "research/check_wave_a_support_aperture_evidence.py"
spec = importlib.util.spec_from_file_location("wave_a_evidence_checker", CHECKER)
assert spec is not None and spec.loader is not None
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class EvidenceCustodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.evidence = Path(self.temporary.name) / "evidence"
        shutil.copytree(checker.DEFAULT_EVIDENCE, self.evidence)

    def test_original_evidence_binds_without_semantic_grading(self) -> None:
        result = checker.check_evidence(self.evidence)
        self.assertEqual(len(result["observations"]), 2)
        self.assertEqual(result["semantic_adjudication"], "NOT_PERFORMED_BY_CHECKER")

    def test_missing_provider_evidence_fails(self) -> None:
        path = self.evidence / f"frozen/structured-run/raw/{checker.CASE_IDS[0]}.json"
        path.unlink()
        with self.assertRaises(FileNotFoundError):
            checker.check_evidence(self.evidence)

    def test_changed_provider_bytes_fail(self) -> None:
        path = self.evidence / f"frozen/structured-run/raw/{checker.CASE_IDS[1]}.json"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(checker.EvidenceError, "preserved hash mismatch"):
            checker.check_evidence(self.evidence)

    def test_rehashed_fabricated_output_still_fails_original_freeze(self) -> None:
        name = "frozen/structured-run/outputs.jsonl"
        path = self.evidence / name
        fabricated = path.read_bytes().replace(b"two traceable weights", b"nine traceable weights")
        path.write_bytes(fabricated)
        manifest_path = self.evidence / "evidence-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"][name].update(sha256=checker.sha256(fabricated), bytes=len(fabricated))
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(checker.EvidenceError, "original freeze binding mismatch"):
            checker.check_evidence(self.evidence)

    def test_unlisted_payload_is_rejected_before_read(self) -> None:
        manifest_path = self.evidence / "evidence-manifest.json"
        manifest = json.loads(manifest_path.read_bytes())
        manifest["files"]["unlisted-payload.jsonl"] = {"sha256": "0" * 64, "bytes": 0}
        manifest_path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(checker.EvidenceError, "evidence file allowlist mismatch"):
            checker.check_evidence(self.evidence)

    def test_duplicate_case_identity_is_rejected(self) -> None:
        with self.assertRaisesRegex(checker.EvidenceError, "duplicate case identity"):
            checker.unique_rows([{"case_id": "A07"}, {"case_id": "A07"}])


if __name__ == "__main__":
    unittest.main()
