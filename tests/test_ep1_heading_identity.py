"""Pin ep1 identity behavior, without asserting a semantic authority decision."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from biotech_rag_assistant.corpus import CorpusValidationError
from biotech_rag_assistant.evidence_packet import packet_identity_valid
from research.check_ep1_heading_identity import (
    fixture_packet,
    mutate_nomination,
    observe_identity,
)


class Ep1HeadingIdentityTests(unittest.TestCase):
    def test_heading_only_mutation_preserves_identity_and_prepares_without_transport(self):
        receipt = observe_identity()
        self.assertEqual(receipt["status"], "PASS_IDENTITY_CONTRACT_OBSERVATION")
        self.assertEqual(receipt["observation"]["changed_nomination_fields"], ["section_heading"])
        self.assertEqual(receipt["provider_transport_calls"], 0)
        self.assertFalse(receipt["semantic_authority_decided_by_checker"])

    def test_source_span_mutation_invalidates_declared_packet(self):
        packet = fixture_packet()
        changed = mutate_nomination(packet, "char_end", packet.admitted_nominations[0].char_end + 1)
        self.assertFalse(packet_identity_valid(changed))

    def test_source_hash_mutation_invalidates_declared_packet(self):
        packet = fixture_packet()
        changed = mutate_nomination(packet, "source_hash", "sha256:" + "0" * 64)
        self.assertFalse(packet_identity_valid(changed))

    def test_body_text_is_not_directly_authenticated_by_ep1(self):
        packet = fixture_packet()
        changed = mutate_nomination(packet, "text", "Deliberately altered fixture body.")
        self.assertTrue(packet_identity_valid(changed))

    def test_missing_native_fixture_cannot_produce_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(CorpusValidationError):
                observe_identity(Path(temporary))


if __name__ == "__main__":
    unittest.main()
