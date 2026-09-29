from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALUATOR = ROOT / "research/evaluate_live_generation_dev_outputs.py"


def load_evaluator_module():
    spec = importlib.util.spec_from_file_location(
        "evaluate_live_generation_dev_outputs",
        EVALUATOR,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_bundle(tmp_path: Path) -> Path:
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    prompt = b"frozen prompt\n"
    wave_a = b'{"case_id":"A01","packet":{}}\n'
    wave_b = b'{"case_id":"B01","packet":{}}\n'

    (bundle / "prompt.txt").write_bytes(prompt)
    (bundle / "wave-a-probes.jsonl").write_bytes(wave_a)

    manifest = {
        "files": {
            "prompt.txt": digest(prompt),
            "wave-a-probes.jsonl": digest(wave_a),
            "wave-b-v21-dev.jsonl": digest(wave_b),
        }
    }
    (bundle / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True),
        encoding="utf-8",
    )
    return bundle


def test_wave_a_verification_does_not_require_or_read_wave_b(
    tmp_path: Path,
) -> None:
    module = load_evaluator_module()
    bundle = make_bundle(tmp_path)

    manifest, manifest_hash, errors = module.verify_bundle(
        bundle,
        wave="a",
    )

    assert errors == []
    assert "wave-b-v21-dev.jsonl" in manifest["files"]
    assert not (bundle / "wave-b-v21-dev.jsonl").exists()
    assert manifest_hash == digest((bundle / "manifest.json").read_bytes())


def test_wave_b_verification_requires_wave_b(tmp_path: Path) -> None:
    module = load_evaluator_module()
    bundle = make_bundle(tmp_path)

    _manifest, _manifest_hash, errors = module.verify_bundle(
        bundle,
        wave="b",
    )

    assert errors == [
        "missing selected bundle file: wave-b-v21-dev.jsonl"
    ]
