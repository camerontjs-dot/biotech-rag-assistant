#!/usr/bin/env python3
"""Run one schema-constrained Ollama Wave A pass with exact raw receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
from urllib import request

from biotech_rag_assistant.evidence_packet import EvidencePacket
from biotech_rag_assistant.ollama_generator import (
    SHADOW_GENERATION_PROMPT_SHA256,
    OllamaGenerator,
    OllamaOptions,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get_json(url: str, timeout: float) -> tuple[bytes, object]:
    req = request.Request(url, method="GET")
    with request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    return raw, json.loads(raw)


def jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def find_model_digest(tags: object, model_id: str) -> str | None:
    if not isinstance(tags, dict):
        return None
    models = tags.get("models")
    if not isinstance(models, list):
        return None
    for row in models:
        if not isinstance(row, dict):
            continue
        if row.get("name") == model_id or row.get("model") == model_id:
            digest = row.get("digest")
            return digest if isinstance(digest, str) else None
    return None


def write_outputs(path: Path, rows: list[dict]) -> None:
    content = "".join(
        json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    )
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--expected-model-digest", required=True)
    parser.add_argument("--expected-manifest-sha256", required=True)
    parser.add_argument(
        "--expected-prompt-sha256",
        default=SHADOW_GENERATION_PROMPT_SHA256,
    )
    parser.add_argument("--expected-schema-sha256", required=True)
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:11434",
    )
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()

    bundle = args.bundle.resolve()
    out = args.out.resolve()
    raw_dir = out / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = bundle / "manifest.json"
    prompt_path = bundle / "prompt.txt"
    wave_a_path = bundle / "wave-a-probes.jsonl"

    observed_manifest = sha256(manifest_path)
    observed_prompt = sha256(prompt_path)
    if observed_manifest != args.expected_manifest_sha256:
        raise SystemExit(
            "bundle manifest hash mismatch: "
            f"{observed_manifest} != {args.expected_manifest_sha256}"
        )
    if observed_prompt != args.expected_prompt_sha256:
        raise SystemExit(
            "prompt hash mismatch: "
            f"{observed_prompt} != {args.expected_prompt_sha256}"
        )

    prompt_text = prompt_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_wave_a = manifest["files"]["wave-a-probes.jsonl"]
    observed_wave_a = sha256(wave_a_path)
    if observed_wave_a != expected_wave_a:
        raise SystemExit(
            f"Wave A hash mismatch: {observed_wave_a} != {expected_wave_a}"
        )

    base_url = args.base_url.rstrip("/")
    tags_raw, tags = get_json(
        f"{base_url}/api/tags",
        args.timeout_seconds,
    )
    tags_path = out / "ollama-tags-response.json"
    tags_path.write_bytes(tags_raw)
    observed_digest = find_model_digest(tags, args.model)
    if observed_digest != args.expected_model_digest:
        raise SystemExit(
            "model digest mismatch: "
            f"{observed_digest!r} != {args.expected_model_digest!r}"
        )

    schema_hash = hashlib.sha256(
        json.dumps(
            OllamaGenerator.output_schema(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    if schema_hash != args.expected_schema_sha256:
        raise SystemExit(
            "GeneratedAnswer schema hash mismatch: "
            f"{schema_hash} != {args.expected_schema_sha256}"
        )

    options = OllamaOptions()
    generator = OllamaGenerator(
        model_id=args.model,
        base_url=base_url,
        prompt_text=prompt_text,
        options=options,
        timeout_seconds=args.timeout_seconds,
    )

    rows = jsonl(wave_a_path)
    outputs: list[dict] = []
    raw_hashes: dict[str, str] = {}
    provider_models: dict[str, str | None] = {}
    skipped: list[str] = []
    outputs_path = out / "outputs.jsonl"

    for row in rows:
        case_id = row["case_id"]
        if not row["generator_should_be_called"]:
            skipped.append(case_id)
            continue

        packet = EvidencePacket.model_validate(row["packet"])
        receipt = generator.generate_with_receipt(packet)

        raw_path = raw_dir / f"{case_id}.json"
        raw_path.write_bytes(receipt.raw_http_body)
        raw_hashes[case_id] = sha256(raw_path)
        model_value = receipt.envelope.get("model")
        provider_models[case_id] = (
            model_value if isinstance(model_value, str) else None
        )
        if model_value != args.model:
            raise SystemExit(
                f"provider model mismatch for {case_id}: {model_value!r}"
            )
        if receipt.envelope.get("done") is not True:
            raise SystemExit(
                f"provider response was not terminal for {case_id}"
            )

        outputs.append(
            {
                "case_id": case_id,
                "raw_output": receipt.parsed_output,
            }
        )
        write_outputs(outputs_path, outputs)

    if generator.call_count != sum(
        bool(row["generator_should_be_called"])
        for row in rows
    ):
        raise SystemExit(
            "model call count differs from callable Wave A case count"
        )

    raw_manifest = {
        "schema_version": "ollama-wave-a-raw-v1",
        "provider": "ollama",
        "model_id": args.model,
        "model_digest": observed_digest,
        "raw_response_sha256": dict(sorted(raw_hashes.items())),
        "tags_response_sha256": sha256(tags_path),
    }
    raw_manifest_path = out / "raw-manifest.json"
    raw_manifest_path.write_text(
        json.dumps(raw_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    metadata = {
        "provider": "ollama",
        "model_id": args.model,
        "model_digest": observed_digest,
        "parameters_or_effort": options.model_dump(),
        "prompt_sha256": observed_prompt,
        "bundle_manifest_sha256": observed_manifest,
        "wave_a_sha256": observed_wave_a,
        "generated_answer_schema_sha256": schema_hash,
        "isolation_notes": (
            "Runner reads manifest, prompt, and Wave A only. "
            "Ollama receives prompt plus one EvidencePacket per request. "
            "No tools, retriever, web, or repository handle is supplied."
        ),
        "fresh_context_policy": (
            "One /api/generate request per callable case, raw=true, "
            "stream=false, keep_alive=0, no context reuse, no retries."
        ),
        "ollama_base_url": base_url,
        "python": platform.python_version(),
        "callable_case_count": generator.call_count,
        "skipped_empty_packet_case_ids": skipped,
        "provider_reported_models": provider_models,
    }
    metadata_path = out / "run_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    report = {
        "disposition": "PASS_OLLAMA_STRUCTURED_WAVE_A_EXECUTION",
        "model_id": args.model,
        "model_digest": observed_digest,
        "manifest_sha256": observed_manifest,
        "prompt_sha256": observed_prompt,
        "wave_a_sha256": observed_wave_a,
        "actual_model_calls": generator.call_count,
        "skipped_case_ids": skipped,
        "outputs_sha256": sha256(outputs_path),
        "run_metadata_sha256": sha256(metadata_path),
        "raw_manifest_sha256": sha256(raw_manifest_path),
        "raw_response_count": len(raw_hashes),
        "retries": 0,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
