"""Construction checks only: never launch the runtime under qualification."""

import subprocess
import unittest
from unittest.mock import patch

import adapter


class ConstructionChecks(unittest.TestCase):
    def test_successful_denied_read_is_falsification(self):
        data = b"opaque-fixture"
        self.assertEqual(
            adapter.classify_read(0, data, b"", adapter.digest(data), denied=True),
            "FALSIFIED",
        )

    def test_missing_target_is_not_denial(self):
        self.assertEqual(
            adapter.classify_read(1, b"", b"No such file", "x", denied=True),
            "INCONCLUSIVE",
        )

    def test_embedded_sentinel_is_not_denial(self):
        data = b"opaque-fixture"
        self.assertEqual(
            adapter.classify_read(1, b"", b"Permission denied " + data, adapter.digest(data),
                                  denied=True, expected_bytes=data),
            "FALSIFIED",
        )

    def test_refusing_valid_allowed_read_is_falsification(self):
        self.assertEqual(
            adapter.classify_read(1, b"", b"Permission denied", "x"),
            "FALSIFIED",
        )

    def test_backend_absence_is_not_a_pass(self):
        binding = {"cli": "missing", "root": "/fixture/role"}
        with patch.object(subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                adapter.invoke(binding, {}, ["/bin/true"])

    def test_wrong_positive_bytes_are_invalid(self):
        self.assertEqual(
            adapter.classify_read(0, b"wrong", b"", adapter.digest(b"right")),
            "APPARATUS_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
