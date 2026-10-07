#!/usr/bin/env python3
"""Mutation check for the v2 schema-contract tests. Offline: no provider, no network.

Each mutant breaks the tuple builder or the gate in one named way. The relevant v2 test
classes must fail for it. The unmutated control must pass. Exit status 0 only when the
control passes and every mutant is killed. A surviving mutant means a test is too weak.
"""

import argparse
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


def load(root):
    sys.dont_write_bytecode = True
    sys.path[:0] = [str(root / "research"), str(root / "src")]
    import test_semantic_author_slot_boundary_v2 as tests

    return tests


def run(classes):
    suite = unittest.TestSuite()
    for case in classes:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    failing = len(result.failures) + len(result.errors)
    names = sorted({str(test).split(" ")[0] for test, _ in result.failures + result.errors})
    return {"tests_run": result.testsRun, "failing_results": failing, "failing_tests": names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    tests = load(args.root.resolve())
    boundary = tests.boundary
    original_tuple = boundary.tuple_schema
    original_gate = boundary.boolean_subschemas

    def without(key):
        def build(definition, assignments):
            schema = original_tuple(definition, assignments)
            schema.pop(key, None)
            return schema
        return build

    def no_positional_const(definition, assignments):
        schema = original_tuple(definition, assignments)
        for position in schema.get("prefixItems", []):
            position["allOf"] = position["allOf"][:1]
        return schema

    def loose_empty(definition, assignments):
        return {"type": "array"} if not assignments else original_tuple(definition, assignments)

    def v1_closed(definition, assignments):
        schema = original_tuple(definition, assignments)
        schema["items"] = False
        return schema

    schema_classes = [tests.ProviderFacingSchemas]
    gate_classes = [tests.ProviderSchemaGate]
    mutants = [
        ("M1 v1 construct restored: items false", "tuple_schema", v1_closed, schema_classes),
        ("M2 maxItems dropped", "tuple_schema", without("maxItems"), schema_classes),
        ("M3 minItems dropped", "tuple_schema", without("minItems"), schema_classes),
        ("M4 positional const dropped", "tuple_schema", no_positional_const, schema_classes),
        ("M5 exactly-empty tuple loses its cardinality", "tuple_schema", loose_empty,
         schema_classes),
        ("M6 prefixItems dropped", "tuple_schema", without("prefixItems"), schema_classes),
        ("G1 gate ignores items", "boolean_subschemas",
         lambda schema: [p for p in original_gate(schema) if not p.endswith("/items")],
         gate_classes),
        ("G2 gate never reports", "boolean_subschemas", lambda schema: [], gate_classes),
    ]
    report = {"control": run(schema_classes + gate_classes), "mutants": []}
    survivors = []
    for label, target, replacement, classes in mutants:
        with mock.patch.object(boundary, target, replacement):
            outcome = run(classes)
        outcome.update(mutant=label, killed=outcome["failing_results"] > 0)
        report["mutants"].append(outcome)
        if not outcome["killed"]:
            survivors.append(label)
    report["control_passes"] = report["control"]["failing_results"] == 0
    report["survivors"] = survivors
    print(json.dumps(report, indent=1, sort_keys=True))
    return 0 if report["control_passes"] and not survivors else 1


if __name__ == "__main__":
    raise SystemExit(main())
