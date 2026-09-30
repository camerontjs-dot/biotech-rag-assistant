"""Preparation disconnection/drift probes; never a v2 reducer test or run."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/check_qualifier_grounding_v2_preparation.py"
SPEC = importlib.util.spec_from_file_location("v2_preparation", SOURCE)
PREP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PREP)


@pytest.fixture
def package(tmp_path):
    for relative in [PREP.NORM, PREP.PREP, PREP.LEGACY,
                     Path("research/evidence/qualifier-grounding-offline-qualification-v1")]:
        shutil.copytree(ROOT / relative, tmp_path / relative)
    experiment = PREP.load(tmp_path, PREP.PREP / "EXPERIMENT.json")
    predecessor = PREP.load(tmp_path, PREP.PREP / "predecessor-custody.json")
    for relative in set(experiment["artifacts"]) | set(predecessor["files"]):
        target = tmp_path / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
    return tmp_path


def reseal(root, filename):
    """Test-only custody update lets structural probes pass the initial hash gate."""
    frozen_path = PREP.FRESH / "freeze.json"
    frozen = PREP.load(root, frozen_path)
    frozen["files"][filename] = PREP.sha(root / PREP.FRESH / filename)
    (root / frozen_path).write_text(json.dumps(frozen))
    experiment_path = PREP.PREP / "EXPERIMENT.json"
    experiment = PREP.load(root, experiment_path)
    for relative in experiment["artifacts"]:
        experiment["artifacts"][relative] = PREP.sha(root / relative)
    (root / experiment_path).write_text(json.dumps(experiment))


def change_output(root, predicate, mutation):
    rows = PREP.lines(root, PREP.FRESH / "expectations.jsonl")
    selected = next(row for row in rows if predicate(row))
    mutation(selected)
    (root / PREP.FRESH / "expectations.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows)
    )
    reseal(root, "expectations.jsonl")


def test_frozen_package_structural_checks():
    receipt = PREP.check_package(ROOT)
    assert receipt["status"] == "PASS_PREPARATION_ONLY"
    assert receipt["v2_decisive_execution"] == "NOT_RUN"


def test_missing_fresh_inputs_fails_closed(package):
    (package / PREP.FRESH / "inputs.jsonl").unlink()
    with pytest.raises(PREP.PreparationError, match="missing artifact"):
        PREP.check_package(package)


def test_expectation_drift_is_detected(package):
    path = package / PREP.FRESH / "expectations.jsonl"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(PREP.PreparationError, match="hash mismatch"):
        PREP.check_package(package)


def test_duplicate_case_is_not_silently_overwritten(package):
    rows = PREP.lines(package, PREP.FRESH / "expectations.jsonl")
    path = package / PREP.FRESH / "expectations.jsonl"
    path.write_text(path.read_text() + json.dumps(rows[0]) + "\n")
    reseal(package, "expectations.jsonl")
    with pytest.raises(PREP.PreparationError, match="duplicate expected case"):
        PREP.check_package(package)


def test_missing_expected_case_is_detected(package):
    rows = PREP.lines(package, PREP.FRESH / "expectations.jsonl")
    (package / PREP.FRESH / "expectations.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows[1:])
    )
    reseal(package, "expectations.jsonl")
    with pytest.raises(PREP.PreparationError, match="missing/extra expectation"):
        PREP.check_package(package)


def test_unknown_output_field_is_not_accepted(package):
    change_output(package, lambda row: True, lambda row: row.update(answer_text="unexpected"))
    with pytest.raises(PREP.PreparationError, match="invalid expectation schema"):
        PREP.check_package(package)


def test_global_uncertainty_cannot_leak_local_authority(package):
    change_output(package, lambda row: row["assessment_status"] == "INCONCLUSIVE",
                  lambda row: row["apertures"].update(N="SUPPORTED"))
    with pytest.raises(PREP.PreparationError, match="global uncertainty leaks"):
        PREP.check_package(package)


def test_rejected_diagnostics_cannot_be_retained_output(package):
    change_output(package, lambda row: row["action"] == "REJECT_COMPLETE",
                  lambda row: row.update(gap_ids=["diagnostic-only"]))
    with pytest.raises(PREP.PreparationError, match="diagnostics presented as retained"):
        PREP.check_package(package)


def test_complete_retention_cannot_drop_obligation(package):
    change_output(package, lambda row: row["action"] == "KEEP_FULL",
                  lambda row: row.update(core_ids=[]))
    with pytest.raises(PREP.PreparationError, match="not exhaustively retained"):
        PREP.check_package(package)


def test_unauthorized_retained_witness_rejected(package):
    change_output(package, lambda row: row["action"] == "KEEP_FULL",
                  lambda row: row.update(witness_ids=["unregistered-witness"]))
    with pytest.raises(PREP.PreparationError, match="unauthorized output witness"):
        PREP.check_package(package)


def test_pair_cannot_omit_required_fields(package):
    path = PREP.FRESH / "pairs.json"
    pairs = PREP.load(package, path)
    pair = next(row for row in pairs["pairs"] if row["relation"] == "INVARIANT")
    pair["compare_fields"] = []
    (package / path).write_text(json.dumps(pairs))
    reseal(package, "pairs.json")
    with pytest.raises(PREP.PreparationError, match="omits required output"):
        PREP.check_package(package)


def test_regression_is_never_relabelled_fresh(package):
    path = PREP.PREP / "regression.json"
    data = PREP.load(package, path)
    data["native_v2_acceptance_key"] = True
    (package / path).write_text(json.dumps(data))
    with pytest.raises(PREP.PreparationError, match="legacy key misrepresented"):
        PREP.check_package(package)


def test_path_injection_fails_before_read(package):
    path = PREP.FRESH / "freeze.json"
    frozen = PREP.load(package, path)
    frozen["files"]["../../outside.json"] = "0" * 64
    (package / path).write_text(json.dumps(frozen))
    with pytest.raises(PREP.PreparationError, match="unsafe artifact reference"):
        PREP.check_package(package)


def test_execution_state_cannot_be_simulated(package):
    path = PREP.PREP / "EXPERIMENT.json"
    data = PREP.load(package, path)
    data["execution"] = "PASS"
    (package / path).write_text(json.dumps(data))
    with pytest.raises(PREP.PreparationError, match="preparation implies execution"):
        PREP.check_package(package)


def test_guard_integer_does_not_masquerade_as_boolean():
    assert PREP.schema_errors({"enum": [True, False, None]}, 1)
    assert PREP.schema_errors({"enum": [True, False, None]}, 0)
    assert not PREP.schema_errors({"enum": [True, False, None]}, True)


def test_unknown_schema_does_not_silently_skip_checks():
    with pytest.raises(PREP.PreparationError, match="unsupported schema keyword"):
        PREP.schema_errors({"unsupportedContract": True}, {})


def test_duplicate_json_key_fails_closed():
    with pytest.raises(PREP.PreparationError, match="duplicate JSON key"):
        json.loads('{"action":"KEEP_FULL","action":"STOP"}',
                   object_pairs_hook=PREP.pairs_object)


def test_schema_requires_fields_without_constructing_answers():
    interface = PREP.load(ROOT, PREP.NORM / "interface.json")
    missing = copy.deepcopy(interface["output_schema"])
    assert PREP.schema_errors(missing, {})


def test_invariant_leaf_coverage_is_complete_without_whole_objects():
    interface = PREP.load(ROOT, PREP.NORM / "interface.json")
    paths = PREP.schema_leaf_paths(interface["output_schema"])
    assert {"apertures.Q", "apertures.N", "apertures.P"} <= paths
    assert "diagnostics.local_apertures.N" in paths
    assert "apertures" not in paths
