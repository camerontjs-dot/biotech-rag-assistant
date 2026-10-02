"""Fake transport controls for exact custody, denial, interruption and no retries."""

import tempfile
import unittest
from pathlib import Path

from build_semantic_author_requests import locate
from run_semantic_request_once import build_request, decoded, encoded, run_once, sha, verify_freeze

CONFIG = {"model": "structural-token", "model_digest": "a" * 64, "provider_version": "0.test",
          "options": {"temperature": 0, "seed": 37}, "timeout_seconds": 1}
SPEC = {"role_instruction": "Return the uninterpreted token.", "artifacts": [], "data": {},
        "output_schema": {"type": "object", "properties": {"token": {"const": "xyz"}},
                          "required": ["token"], "additionalProperties": False}}


class Controls(unittest.TestCase):
    def fake(self, post_raw=None, disconnected=False, digest="a" * 64):
        self.calls = []

        def transport(method, endpoint, body=None, timeout=10):
            self.calls.append((method, endpoint, body))
            if endpoint == "/api/version":
                raw = encoded({"version": "0.test"})
            elif endpoint == "/api/tags":
                raw = encoded({"models": [{"name": "structural-token", "digest": digest}]})
            else:
                if disconnected:
                    raise ConnectionError("disconnected")
                raw = post_raw or encoded({"model": "structural-token", "done": True,
                                          "done_reason": "stop", "response": '{"token":"xyz"}'})
            return 200, [("Content-Type", "application/json")], raw, None

        return transport

    def test_exact_bytes_and_raw_capture(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "call"
            receipt, parsed = run_once(SPEC, CONFIG, output, self.fake())
            self.assertEqual(receipt["status"], "PASS_REQUEST_PATH_ONLY")
            self.assertEqual(parsed, {"token": "xyz"})
            sent = self.calls[-1][2]
            self.assertEqual(sent, (output / "request.json").read_bytes())
            self.assertEqual(sha(sent), receipt["request_sha256"])
            self.assertEqual(sha((output / "provider-response.raw.json").read_bytes()),
                             receipt["raw_response_sha256"])
            self.assertEqual(set(decoded(sent)), {"model", "prompt", "raw", "stream",
                                                  "keep_alive", "format", "options"})
            self.assertEqual(len([c for c in self.calls if c[0] == "POST"]), 1)

    def test_disconnection_is_preserved_and_never_retried(self):
        with tempfile.TemporaryDirectory() as name:
            receipt, _ = run_once(SPEC, CONFIG, Path(name) / "call", self.fake(disconnected=True))
            self.assertEqual(receipt["status"], "APPARATUS_INVALID")
            self.assertEqual(receipt["generation_attempts"], 1)
            self.assertEqual(len([c for c in self.calls if c[0] == "POST"]), 1)
            self.assertIn("disconnected", receipt["errors"][0])

    def test_malformed_or_contradictory_output_remains_raw(self):
        for response in ('{"token":"wrong"}', '{"token":"xyz","token":"other"}',
                         '{"token":NaN}'):
            with self.subTest(response=response), tempfile.TemporaryDirectory() as name:
                raw = encoded({"model": "structural-token", "done": True,
                               "done_reason": "stop", "response": response})
                output = Path(name) / "call"
                receipt, _ = run_once(SPEC, CONFIG, output, self.fake(post_raw=raw))
                self.assertEqual(receipt["status"], "APPARATUS_INVALID")
                self.assertEqual((output / "provider-response.raw.json").read_bytes(), raw)

    def test_drift_blocks_generation(self):
        with tempfile.TemporaryDirectory() as name:
            receipt, _ = run_once(SPEC, CONFIG, Path(name) / "call", self.fake(digest="b" * 64))
            self.assertEqual(receipt["generation_attempts"], 0)
            self.assertFalse(any(c[0] == "POST" for c in self.calls))

    def test_injected_handles_and_artifact_drift_are_rejected(self):
        for field in ("tools", "context", "messages", "memory", "repository"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_request({**SPEC, field: []}, CONFIG)
        with self.assertRaises(ValueError):
            build_request({**SPEC, "artifacts": [{"reference": "x", "text": "xyz",
                                                  "sha256": "a" * 64}]}, CONFIG)
        with self.assertRaises(ValueError):
            build_request(SPEC, {**CONFIG, "url": "remote"})
        with self.assertRaises(ValueError):
            build_request(SPEC, {**CONFIG, "options": {"tools": []}})

    def test_mechanical_anchor_transform_never_guesses(self):
        self.assertEqual(locate({"text": "xyz"}, "λ xyz!"),
                         {"text": "xyz", "start": 2, "end": 5})
        for needle, text in (("missing", "xyz"), ("xyz", "xyz xyz"), ("", "xyz")):
            with self.subTest(needle=needle), self.assertRaises(ValueError):
                locate({"text": needle}, text)

    def test_interrupted_output_directory_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as name:
            output = Path(name) / "call"
            output.mkdir()
            with self.assertRaises(FileExistsError):
                run_once(SPEC, CONFIG, output, self.fake())
            self.assertEqual(self.calls, [])

    def test_external_schema_and_frozen_file_drift_fail_closed(self):
        with self.assertRaises(ValueError):
            build_request({**SPEC, "output_schema": {"$ref": "https://invalid/schema"}}, CONFIG)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "frozen").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                verify_freeze(root, {"artifacts": {"frozen": sha(b"original")}})


if __name__ == "__main__":
    unittest.main()
