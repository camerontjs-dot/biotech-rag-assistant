"""Implementation-local tests derived only from frozen policy/interface v2."""

import copy
import unittest

from reducer import decide


GUARDS = (
    "core_independently_supported", "bindings_preserved", "required_context_retained",
    "removal_independent", "no_missing_presupposition", "gap_explicit",
)


def witness(identifier, surface, apertures, entails=(), contradicts=(), ambiguous=()):
    return {"id": identifier, "surface": surface, "apertures": list(apertures),
            "entails": list(entails), "contradicts": list(contradicts),
            "ambiguous": list(ambiguous)}


def ledger():
    return {"case_id": "local", "ledger": {
        "coverage": "COMPLETE", "integrity": "VALID",
        "obligations": [{"id": x, "materiality": "MATERIAL"} for x in ("b", "a")],
        "witnesses": [witness("quote", "QUOTE", ["Q"], ["a", "b"]),
                      witness("body", "BODY", ["P", "N"], ["a", "b"])],
        "proposal": None,
    }}


def partial():
    value = ledger()
    value["ledger"]["witnesses"][1]["entails"] = ["a"]
    value["ledger"]["proposal"] = {
        "core_ids": ["a"], "gap_ids": ["b"], "body_witness_ids": ["body"],
        "guards": {g: True for g in GUARDS},
    }
    return value


class PolicyTests(unittest.TestCase):
    def test_full_retention(self):
        value = ledger()
        before = copy.deepcopy(value)
        result = decide(value)
        self.assertEqual(value, before)
        self.assertEqual(result["action"], "KEEP_FULL")
        self.assertEqual(result["core_ids"], ["a", "b"])
        self.assertEqual(result["gap_ids"], [])
        self.assertEqual(result["witness_ids"], ["body"])
        self.assertEqual(result["citation"], "SUFFICIENT")
        self.assertEqual(result["apertures"], dict.fromkeys(("Q", "N", "P"), "SUPPORTED"))
        self.assertEqual(result["diagnostics"]["proposal_status"], "NOT_REQUIRED")

    def test_citation_precedence_and_retention(self):
        for quote_full, nominated, expected in (
            (False, True, "QUOTE_INSUFFICIENT"),
            (True, False, "NOMINATION_INSUFFICIENT"),
            (False, False, "NOMINATION_INSUFFICIENT"),
        ):
            with self.subTest(quote_full=quote_full, nominated=nominated):
                value = ledger()
                if not quote_full:
                    value["ledger"]["witnesses"][0]["entails"] = ["a"]
                if not nominated:
                    value["ledger"]["witnesses"][1]["apertures"] = ["P"]
                result = decide(value)
                self.assertEqual(result["action"], "HOLD_FOR_CITATION")
                self.assertEqual(result["citation"], expected)
                self.assertEqual(result["grounding"], "FULL_BODY_SUPPORT")
                self.assertEqual(result["core_ids"], ["a", "b"])

    def test_partial_projection(self):
        result = decide(partial())
        self.assertEqual(result["action"], "PROPOSE_CORE_WITH_GAP")
        self.assertEqual(result["finding"], "UNSUPPORTED_MATERIAL_QUALIFIER")
        self.assertEqual(result["core_ids"], ["a"])
        self.assertEqual(result["gap_ids"], ["b"])
        self.assertEqual(result["witness_ids"], ["body"])
        self.assertEqual(result["citation"], "NOMINATION_INSUFFICIENT")

    def test_proposal_safety_and_absence(self):
        alterations = [lambda p: p.update(core_ids=[]), lambda p: p.update(gap_ids=[]),
                       lambda p: p.update(gap_ids=["a", "b"]),
                       lambda p: p.update(body_witness_ids=["quote"]),
                       lambda p: p.update(body_witness_ids=[])]
        for alter in alterations:
            value = partial()
            alter(value["ledger"]["proposal"])
            result = decide(value)
            self.assertEqual(result["action"], "REJECT_COMPLETE")
            self.assertEqual(result["finding"], "UNSAFE_DECOMPOSITION")
            self.assertEqual(result["diagnostics"]["proposal_status"], "UNSAFE")
            self.assertEqual(result["core_ids"], [])
        value = partial()
        value["ledger"]["proposal"] = None
        self.assertEqual(decide(value)["diagnostics"]["proposal_status"], "ABSENT")

    def test_each_guard_false_and_null(self):
        for guard in GUARDS:
            for flag, status, action in ((False, "UNSAFE", "REJECT_COMPLETE"),
                                        (None, "UNKNOWN", "WITHHOLD")):
                with self.subTest(guard=guard, flag=flag):
                    value = partial()
                    value["ledger"]["proposal"]["guards"][guard] = flag
                    result = decide(value)
                    self.assertEqual(result["diagnostics"]["proposal_status"], status)
                    self.assertEqual(result["action"], action)

    def test_null_precedes_false_and_inapplicable_guard(self):
        value = partial()
        value["ledger"]["proposal"]["guards"][GUARDS[0]] = False
        value["ledger"]["proposal"]["guards"][GUARDS[1]] = None
        self.assertEqual(decide(value)["action"], "WITHHOLD")
        value["ledger"]["witnesses"][1]["entails"] = ["a", "b"]
        result = decide(value)
        self.assertEqual(result["action"], "KEEP_FULL")
        self.assertEqual(result["diagnostics"]["proposal_status"], "NOT_REQUIRED")

    def test_pure_contradiction_and_zero_support(self):
        value = partial()
        value["ledger"]["witnesses"][1]["contradicts"] = ["b"]
        result = decide(value)
        self.assertEqual(result["action"], "REJECT_COMPLETE")
        self.assertEqual(result["finding"], "CONTRADICTED_CLAIM")
        self.assertEqual(result["diagnostics"]["proposal_status"], "NOT_REQUIRED")
        self.assertEqual(result["diagnostics"]["contradicted_packet_ids"], ["b"])
        value["ledger"]["witnesses"][1]["entails"] = []
        value["ledger"]["witnesses"][1]["contradicts"] = []
        result = decide(value)
        self.assertEqual(result["finding"], "NO_SUPPORTED_CORE")
        self.assertEqual(result["core_ids"], [])

    def test_every_base_uncertainty(self):
        for source in ("COVERAGE_UNKNOWN", "MATERIALITY_UNKNOWN",
                       "AUTHORIZED_AMBIGUITY", "AUTHORIZED_CONFLICT"):
            value = ledger()
            if source == "COVERAGE_UNKNOWN":
                value["ledger"]["coverage"] = "UNKNOWN"
            elif source == "MATERIALITY_UNKNOWN":
                value["ledger"]["obligations"][0]["materiality"] = "UNKNOWN"
            elif source == "AUTHORIZED_AMBIGUITY":
                value["ledger"]["witnesses"][0]["ambiguous"] = ["a"]
            else:
                value["ledger"]["witnesses"].append(witness("other", "BODY", ["P"], contradicts=["a"]))
            result = decide(value)
            self.assertEqual(result["action"], "WITHHOLD")
            self.assertEqual(result["apertures"], dict.fromkeys(("Q", "N", "P"), "INCONCLUSIVE"))
            self.assertEqual(result["citation"], "INCONCLUSIVE")
            self.assertEqual(result["diagnostics"]["uncertainty_sources"], [source])
            self.assertEqual(result["diagnostics"]["proposal_status"], "NOT_ASSESSED")
            self.assertEqual(result["core_ids"], [])

    def test_partial_witness_union_and_silence(self):
        value = ledger()
        value["ledger"]["witnesses"][1]["entails"] = ["a"]
        value["ledger"]["witnesses"].extend([
            witness("other", "BODY", ["N", "P"], ["b"]),
            witness("silent", "BODY", ["P"]),
        ])
        result = decide(value)
        self.assertEqual(result["action"], "KEEP_FULL")
        self.assertEqual(result["witness_ids"], ["body", "other"])
        self.assertEqual(result["diagnostics"]["considered_witness_ids"], ["body", "other", "quote"])

    def test_unauthorized_surfaces_are_silent(self):
        value = ledger()
        for surface in ("QUERY", "HEADING", "METADATA"):
            value["ledger"]["witnesses"].append(witness(surface, surface, [], ["a", "b"], ["a"], ["b"]))
        self.assertEqual(decide(value), decide(ledger()))

    def test_cross_aperture_contradiction_is_not_body_conflict(self):
        value = ledger()
        value["ledger"]["witnesses"][0]["entails"] = []
        value["ledger"]["witnesses"][0]["contradicts"] = ["a"]
        result = decide(value)
        self.assertEqual(result["action"], "HOLD_FOR_CITATION")
        self.assertEqual(result["diagnostics"]["conflicting_ids"], [])

    def test_integrity_and_invalid_input_precedence(self):
        for integrity in ("UNKNOWN", "CUSTODY_INVALID", "ASSESSOR_UNAVAILABLE", "EXECUTION_FAILURE"):
            value = ledger()
            value["ledger"]["integrity"] = integrity
            value["ledger"]["coverage"] = "UNKNOWN"
            result = decide(value)
            self.assertEqual(result["action"], "STOP")
            self.assertEqual(result["diagnostics"]["considered_witness_ids"], [])
            self.assertEqual(result["diagnostics"]["uncertainty_sources"], [])
            expected = "INTEGRITY_UNKNOWN" if integrity == "UNKNOWN" else "INTEGRITY_NOT_VALID"
            self.assertEqual(result["diagnostics"]["apparatus_code"], expected)
            value["ledger"]["extra"] = None
            self.assertEqual(decide(value)["diagnostics"]["apparatus_code"], "INVALID_INPUT")

    def test_interface_rejections_and_case_recovery(self):
        changes = [lambda v: v.update(extra=None), lambda v: v["ledger"].pop("proposal"),
                   lambda v: v["ledger"].update(obligations=[]),
                   lambda v: v["ledger"]["obligations"].append(v["ledger"]["obligations"][0]),
                   lambda v: v["ledger"]["witnesses"].append(v["ledger"]["witnesses"][0]),
                   lambda v: v["ledger"]["witnesses"][0].update(entails=["unknown"]),
                   lambda v: v["ledger"]["witnesses"][0].update(entails=["a", "a"]),
                   lambda v: v["ledger"]["witnesses"][0].update(apertures=["P"]),
                   lambda v: v["ledger"]["witnesses"][1].update(apertures=["N"]),
                   lambda v: v["ledger"]["witnesses"][1].update(apertures=["Q", "P"])]
        for change in changes:
            value = ledger()
            change(value)
            result = decide(value)
            self.assertEqual(result["case_id"], "local")
            self.assertEqual(result["diagnostics"]["apparatus_code"], "INVALID_INPUT")
        for value in (None, [], {}, {"case_id": ""}, {"case_id": 3}):
            result = decide(value)
            self.assertEqual(result["case_id"], None)
            self.assertEqual(result["action"], "STOP")
        value = partial()
        value["ledger"]["proposal"]["guards"][GUARDS[0]] = 1
        self.assertEqual(decide(value)["action"], "STOP")

    def test_namespace_overlap_and_opaque_names(self):
        value = ledger()
        value["case_id"] = "a"
        value["ledger"]["witnesses"][1]["id"] = "a"
        result = decide(value)
        self.assertEqual(result["action"], "KEEP_FULL")
        self.assertEqual(result["witness_ids"], ["a"])
        rename = {"a": "Ω", "b": "A"}
        for obligation in value["ledger"]["obligations"]:
            obligation["id"] = rename[obligation["id"]]
        for w in value["ledger"]["witnesses"]:
            for key in ("entails", "contradicts", "ambiguous"):
                w[key] = [rename[x] for x in w[key]]
        renamed = decide(value)
        self.assertEqual(renamed["action"], result["action"])
        self.assertEqual(renamed["core_ids"], ["A", "Ω"])

    def test_order_and_repetition(self):
        value = ledger()
        expected = decide(value)
        value["ledger"]["obligations"].reverse()
        value["ledger"]["witnesses"].reverse()
        for w in value["ledger"]["witnesses"]:
            w["entails"].reverse()
            w["apertures"].reverse()
        self.assertEqual(decide(value), expected)
        self.assertEqual(decide(value), expected)


if __name__ == "__main__":
    unittest.main()
