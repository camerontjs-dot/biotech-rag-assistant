"""Construction checks only. They do not qualify the runtime."""

import subprocess
import unittest

from adapter import classify_read, environment, invoke


class ConstructionChecks(unittest.TestCase):
    def result(self, code, out=b"", err=b""):
        return subprocess.CompletedProcess([], code, out, err)

    def test_successful_denied_read_falsifies(self):
        self.assertEqual(classify_read(self.result(0, b"sentinel"), b"sentinel", True),
                         "FALSIFIED")

    def test_partial_stdout_falsifies_even_with_denial(self):
        self.assertEqual(classify_read(self.result(1, b"s", b"Permission denied"),
                                       b"sentinel", True), "FALSIFIED")

    def test_missing_target_is_not_denial(self):
        self.assertEqual(classify_read(self.result(1, err=b"No such file or directory"),
                                       b"sentinel", True), "APPARATUS_INVALID")

    def test_stderr_leak_falsifies(self):
        self.assertEqual(classify_read(self.result(1, err=b"Permission denied ABCDEFGHIJ"),
                                       b"ABCDEFGHIJKL", True), "FALSIFIED")

    def test_unrelated_failure_does_not_pass(self):
        self.assertEqual(classify_read(self.result(1, err=b"unexpected fault"),
                                       b"sentinel", True), "INCONCLUSIVE")

    def test_allowed_refusal_falsifies(self):
        self.assertEqual(classify_read(self.result(1, err=b"cat: target: Operation not permitted"),
                                       b"sentinel"), "FALSIFIED")

    def test_sandbox_startup_failure_is_not_file_denial(self):
        self.assertEqual(classify_read(self.result(
            71, err=b"sandbox-exec: sandbox_apply: Operation not permitted"
        ), b"sentinel", True), "APPARATUS_INVALID")

    def test_valid_native_denial_passes(self):
        self.assertEqual(classify_read(self.result(
            1, err=b"cat: target: Operation not permitted"
        ), b"sentinel", True), "PASS")

    def test_wrong_allowed_bytes_invalid(self):
        self.assertEqual(classify_read(self.result(0, b"different"), b"sentinel"),
                         "APPARATUS_INVALID")

    def test_backend_absence_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            invoke({"cli": "/nonexistent-preflight-backend", "role_root": "/",
                    "config_homes": {"baseline": "/"}}, ["/usr/bin/true"])

    def test_parent_environment_is_not_inherited(self):
        actual = environment({"config_homes": {"baseline": "fixture-config"}})
        self.assertEqual(set(actual), {"PATH", "LANG", "CODEX_HOME"})
        self.assertEqual(actual["CODEX_HOME"], "fixture-config")


if __name__ == "__main__":
    unittest.main()
