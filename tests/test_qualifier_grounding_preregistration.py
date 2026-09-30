"""Contract selftests only; no generator, provider, replay or semantic candidate."""

from __future__ import annotations

import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from research.check_qualifier_grounding_preregistration import (
    PACKAGE,
    ROOT,
    ContractError,
    check_preregistration,
    digest,
    grade_submission,
    read_json,
    read_rows,
    validate_expectation,
    validate_ledger,
)


def contracts() -> tuple[dict, list[dict], list[dict]]:
    return (read_json(PACKAGE / "interface.json"), read_rows(PACKAGE / "inputs.jsonl"),
            read_rows(PACKAGE / "expectations.jsonl"))


def oracle_probe(expectations: list[dict]) -> dict:
    """Known oracle data exercises the scorer; this is never a candidate result."""
    return {
        "schema_version": "qualifier-grounding-submission/v1",
        "decisions": [{**deepcopy(row["expected"]), "reason": "mechanical contract selftest"}
                      for row in expectations],
    }


def preparation_copy(tmp_path: Path) -> tuple[Path, Path]:
    freeze = read_json(PACKAGE / "freeze.json")
    custody = read_json(PACKAGE / "custody.json")
    for name in set(freeze["files"]) | set(custody["verified_files_sha256"]):
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    package = tmp_path / PACKAGE.relative_to(ROOT)
    shutil.copyfile(PACKAGE / "freeze.json", package / "freeze.json")
    return package, tmp_path


def test_frozen_preparation_contract_has_no_semantic_execution() -> None:
    result = check_preregistration()
    assert result["status"] == "PASS_PREREGISTRATION_CONTRACT_ONLY"
    assert result["qualification"] == "NOT_RUN"
    assert result["semantic_assessor"] == "NOT_IMPLEMENTED"


def test_missing_custody_file_fails_closed(tmp_path: Path) -> None:
    package, root = preparation_copy(tmp_path)
    name = "research/evidence/wave-a-ep1-authority-readjudication-v1/adjudication.json"
    (root / name).unlink()
    with pytest.raises(OSError):
        check_preregistration(package, root)


def test_rehashed_permissive_expectation_is_rejected(tmp_path: Path) -> None:
    package, root = preparation_copy(tmp_path)
    rows = read_rows(package / "expectations.jsonl")
    row = next(row for row in rows if row["case_id"] == "L02")
    row["expected"]["apertures"]["P"] = "SUPPORTED"
    path = package / "expectations.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    freeze = read_json(package / "freeze.json")
    freeze["files"][str(path.relative_to(root))]["sha256"] = digest(path)
    (package / "freeze.json").write_text(json.dumps(freeze))
    with pytest.raises(ContractError, match="declared aperture coverage"):
        check_preregistration(package, root)


def test_changed_historical_bytes_cannot_be_rehashed_into_authority(tmp_path: Path) -> None:
    package, root = preparation_copy(tmp_path)
    path = root / "research/evidence/wave-a-ep1-authority-readjudication-v1/adjudication.json"
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ContractError, match="predecessor pin drift"):
        check_preregistration(package, root)


def test_untrusted_witness_cannot_gain_packet_aperture() -> None:
    interface, inputs, _ = contracts()
    ledger = deepcopy(inputs[1]["ledger"])
    witness = next(row for row in ledger["witnesses"] if row["surface"] == "QUERY")
    witness["apertures"] = ["P"]
    with pytest.raises(ContractError, match="unauthorized witness aperture"):
        validate_ledger(ledger, interface)


def test_supported_condition_cannot_be_discarded_from_gold() -> None:
    _, inputs, expectations = contracts()
    ledger = next(row["ledger"] for row in inputs if row["case_id"] == "L03")
    decision = deepcopy(next(row["expected"] for row in expectations if row["case_id"] == "L03"))
    decision["core_ids"] = ["v0"]
    with pytest.raises(ContractError, match="supported condition discarded"):
        validate_expectation(ledger, decision)


def test_fully_witnessed_body_cannot_be_labeled_unsupported_in_gold() -> None:
    _, inputs, expectations = contracts()
    ledger = next(row["ledger"] for row in inputs if row["case_id"] == "L03")
    decision = deepcopy(next(row["expected"] for row in expectations if row["case_id"] == "L03"))
    decision["apertures"]["P"] = "UNSUPPORTED"
    with pytest.raises(ContractError, match="declared aperture coverage"):
        validate_expectation(ledger, decision)


def test_false_or_unknown_safety_guard_cannot_authorize_projection() -> None:
    _, inputs, expectations = contracts()
    decision = next(row["expected"] for row in expectations if row["case_id"] == "L02")
    for case_id in ("L04", "L05", "L06", "L11", "L24", "L25"):
        ledger = next(row["ledger"] for row in inputs if row["case_id"] == case_id)
        with pytest.raises(ContractError):
            validate_expectation(ledger, decision)


def test_scorer_oracle_selftest_does_not_qualify_a_candidate() -> None:
    interface, _, expectations = contracts()
    probe = grade_submission(oracle_probe(expectations), expectations, interface)
    assert probe["outcome"] == "CONTRACT_MATCH_ONLY"
    assert probe["semantic_input_validity"] == "NOT_DETERMINED_BY_THIS_SCORER"
    assert probe["candidate_source_review"] == "REQUIRED_SEPARATELY"


def test_always_supported_probe_is_falsified_even_when_action_withholds() -> None:
    interface, _, expectations = contracts()
    probe = oracle_probe(expectations)
    for row in probe["decisions"]:
        row["apertures"] = dict.fromkeys(("Q", "N", "P"), "SUPPORTED")
        row["action"] = "WITHHOLD"
    scored = grade_submission(probe, expectations, interface)
    assert scored["outcome"] == "FALSIFIED"
    assert any(row["unsafe_support"] for row in scored["findings"])


def test_always_inconclusive_probe_is_not_a_pass() -> None:
    interface, _, expectations = contracts()
    probe = oracle_probe(expectations)
    for row in probe["decisions"]:
        row.update(assessment_status="INCONCLUSIVE", action="WITHHOLD", core_ids=[], gap_ids=[],
                   witness_ids=[], grounding="INCONCLUSIVE", citation="INCONCLUSIVE",
                   finding="INCONCLUSIVE", apertures=dict.fromkeys(("Q", "N", "P"), "INCONCLUSIVE"))
    assert grade_submission(probe, expectations, interface)["outcome"] == "MATERIALLY_WEAKENED"


@pytest.mark.parametrize("fault", ["absent", "missing", "duplicate", "extra_field"])
def test_absent_or_malformed_candidate_submission_is_apparatus_failure(fault: str) -> None:
    interface, _, expectations = contracts()
    probe = oracle_probe(expectations)
    if fault == "absent":
        probe = None
    elif fault == "missing":
        probe["decisions"].pop()
    elif fault == "duplicate":
        probe["decisions"][-1] = deepcopy(probe["decisions"][0])
    else:
        probe["decisions"][0]["emitted_answer"] = "forbidden output"
    assert grade_submission(probe, expectations, interface)["outcome"] == "APPARATUS_FAILURE"


def test_freeze_cannot_expand_its_read_aperture(tmp_path: Path) -> None:
    package, root = preparation_copy(tmp_path)
    freeze = read_json(package / "freeze.json")
    freeze["files"]["outside-approved-aperture.json"] = {"sha256": "0" * 64}
    (package / "freeze.json").write_text(json.dumps(freeze))
    with pytest.raises(ContractError, match="freeze allowlist"):
        check_preregistration(package, root)
