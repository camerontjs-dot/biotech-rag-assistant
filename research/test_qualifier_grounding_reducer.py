"""Implementation-local checks derived solely from policy/interface declarations.

Synthetic identifiers and assessment structures; no qualification controls imported.
"""

import copy
import unittest

from qualifier_grounding_reducer import decide


def ledger():
    return {
        "case_id": "local-unit",
        "ledger": {
            "coverage": "COMPLETE",
            "integrity": "VALID",
            "obligations": [{"id": "x", "materiality": "MATERIAL"}],
            "witnesses": [
                {
                    "id": "body",
                    "surface": "BODY",
                    "apertures": ["N", "P"],
                    "entails": ["x"],
                    "contradicts": [],
                    "ambiguous": [],
                },
                {
                    "id": "quote",
                    "surface": "QUOTE",
                    "apertures": ["Q"],
                    "entails": ["x"],
                    "contradicts": [],
                    "ambiguous": [],
                },
            ],
            "proposal": None,
        },
    }


def proposal():
    value = ledger()
    value["ledger"]["obligations"].append({"id": "y", "materiality": "MATERIAL"})
    value["ledger"]["proposal"] = {
        "core_ids": ["x"],
        "gap_ids": ["y"],
        "body_witness_ids": ["body"],
        "guards": {
            key: True
            for key in (
                "core_independently_supported",
                "bindings_preserved",
                "required_context_retained",
                "removal_independent",
                "no_missing_presupposition",
                "gap_explicit",
            )
        },
    }
    return value


class ReducerContractTests(unittest.TestCase):
    def test_full_declared_support(self):
        self.assertEqual(decide(ledger())["action"], "KEEP_FULL")

    def test_quote_omission_retains_packet_support(self):
        value = ledger()
        value["ledger"]["witnesses"].pop()
        result = decide(value)
        self.assertEqual(result["action"], "HOLD_FOR_CITATION")
        self.assertEqual(result["grounding"], "FULL_BODY_SUPPORT")
        self.assertEqual(result["gap_ids"], [])

    def test_unauthorized_surfaces_do_not_support_packet(self):
        for surface in ("QUERY", "HEADING", "METADATA", "QUOTE"):
            with self.subTest(surface=surface):
                value = ledger()
                value["ledger"]["witnesses"][0]["surface"] = surface
                self.assertEqual(decide(value)["action"], "REJECT_COMPLETE")

    def test_unknown_coverage_or_materiality_withholds(self):
        for field in ("coverage", "materiality"):
            value = ledger()
            if field == "coverage":
                value["ledger"][field] = "UNKNOWN"
            else:
                value["ledger"]["obligations"][0][field] = "UNKNOWN"
            self.assertEqual(decide(value)["assessment_status"], "INCONCLUSIVE")
            self.assertEqual(decide(value)["action"], "WITHHOLD")

    def test_disconnected_assessment_stops(self):
        value = ledger()
        value["ledger"]["integrity"] = "ASSESSOR_UNAVAILABLE"
        self.assertEqual(decide(value)["assessment_status"], "APPARATUS_FAILURE")
        self.assertEqual(decide(value)["action"], "STOP")

    def test_contradiction_overrides_entailment(self):
        value = proposal()
        value["ledger"]["witnesses"][0]["contradicts"] = ["y"]
        self.assertEqual(decide(value)["finding"], "CONTRADICTED_CLAIM")
        self.assertEqual(decide(value)["action"], "REJECT_COMPLETE")

    def test_ambiguous_body_withholds(self):
        value = ledger()
        value["ledger"]["witnesses"][0]["ambiguous"] = ["x"]
        self.assertEqual(decide(value)["action"], "WITHHOLD")

    def test_core_has_explicit_gap(self):
        result = decide(proposal())
        self.assertEqual(result["action"], "PROPOSE_CORE_WITH_GAP")
        self.assertEqual(result["core_ids"], ["x"])
        self.assertEqual(result["gap_ids"], ["y"])

    def test_false_guard_rejects_and_unknown_guard_withholds(self):
        for state, action in ((False, "REJECT_COMPLETE"), (None, "WITHHOLD")):
            value = proposal()
            value["ledger"]["proposal"]["guards"]["bindings_preserved"] = state
            self.assertEqual(decide(value)["action"], action)

    def test_guard_assertion_cannot_replace_body_witness(self):
        value = proposal()
        value["ledger"]["proposal"]["body_witness_ids"] = ["quote"]
        self.assertEqual(decide(value)["finding"], "UNSAFE_DECOMPOSITION")

    def test_supported_obligation_cannot_be_discarded(self):
        value = proposal()
        value["ledger"]["obligations"].append({"id": "z", "materiality": "MATERIAL"})
        value["ledger"]["witnesses"][0]["entails"].append("z")
        value["ledger"]["proposal"]["gap_ids"].append("z")
        self.assertEqual(decide(value)["finding"], "UNSAFE_DECOMPOSITION")

    def test_malformed_reference_stops(self):
        value = ledger()
        value["ledger"]["witnesses"][0]["entails"] = ["absent"]
        self.assertEqual(decide(value)["action"], "STOP")

    def test_opaque_case_identity_is_passthrough(self):
        value = proposal()
        expected = decide(value)
        value["case_id"] = "arbitrary-renaming"
        actual = decide(value)
        expected.pop("case_id")
        actual.pop("case_id")
        self.assertEqual(actual, expected)

    def test_input_is_unmodified_and_list_order_is_irrelevant(self):
        value = proposal()
        original = copy.deepcopy(value)
        expected = decide(value)
        self.assertEqual(value, original)
        value["ledger"]["obligations"].reverse()
        value["ledger"]["witnesses"].reverse()
        self.assertEqual(decide(value), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
