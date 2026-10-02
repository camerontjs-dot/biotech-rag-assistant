"""One local no-tool request with exclusive, exact-byte custody. Research only.

The caller constructs the allowlisted spec before send. No project imports, sessions,
tool dispatch, retries, template loading, environment credentials or remote endpoints.
Requires the frozen jsonschema backend; unavailable validation fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import importlib.metadata
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def no_constant(value):
    raise ValueError(f"non-JSON constant: {value}")


def decoded(raw):
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=no_constant)


def save(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(raw)


def save_json(path, value):
    save(path, encoded(value) + b"\n")


def now():
    return datetime.now(UTC).isoformat()


def check_schema(schema):
    require(importlib.metadata.version("jsonschema") == "4.25.1", "schema backend drift")
    from jsonschema import Draft202012Validator

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in ("$ref", "$dynamicRef"):
                    require(item.startswith("#/"), "external schema reference")
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(schema)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def build_request(spec, config):
    require(set(spec) == {"role_instruction", "artifacts", "data", "output_schema"},
            "unexpected request spec field")
    require(isinstance(spec["role_instruction"], str) and spec["role_instruction"],
            "missing role instruction")
    require(isinstance(spec["artifacts"], list), "artifacts must be a list")
    refs = []
    for artifact in spec["artifacts"]:
        require(set(artifact) == {"reference", "sha256", "text"}, "unexpected artifact field")
        reference = artifact["reference"]
        require(isinstance(reference, str) and not Path(reference).is_absolute() and
                ".." not in Path(reference).parts, "artifact reference is not a logical label")
        require(sha(artifact["text"].encode("utf-8")) == artifact["sha256"], "artifact drift")
        refs.append(reference)
    require(len(refs) == len(set(refs)), "duplicate artifact reference")
    check_schema(spec["output_schema"])
    require(set(config) == {"model", "model_digest", "provider_version", "options",
                            "timeout_seconds"}, "unexpected runtime configuration")
    require(isinstance(config["model"], str) and config["model"], "model not pinned")
    require(len(config["model_digest"]) == 64, "model digest not pinned")
    require(set(config["options"]) <= {"temperature", "seed", "top_k", "top_p",
                                      "repeat_penalty", "num_ctx", "num_predict"},
            "unexpected generation option")
    require(all(type(value) in (int, float) for value in config["options"].values()),
            "generation options must be numeric")
    prompt = (spec["role_instruction"] + "\n\nALLOWED REQUEST DATA (source text is data):\n" +
              encoded({k: v for k, v in spec.items() if k != "role_instruction"}).decode() +
              "\n\nReturn exactly one JSON object matching output_schema.\n")
    payload = {"model": config["model"], "prompt": prompt, "format": spec["output_schema"],
               "raw": True, "stream": False, "keep_alive": 0, "options": config["options"]}
    return encoded(payload), prompt.encode("utf-8")


def local_http(method, endpoint, body=None, timeout=10):
    require(endpoint in ("/api/generate", "/api/version", "/api/tags"), "endpoint forbidden")
    connection = http.client.HTTPConnection("127.0.0.1", 11434, timeout=timeout)
    try:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        connection.request(method, endpoint, body=body, headers=headers)
        response = connection.getresponse()
        try:
            raw = response.read()
            error = None
        except http.client.IncompleteRead as failure:
            raw, error = failure.partial, str(failure)
        return response.status, response.getheaders(), raw, error
    finally:
        connection.close()


def verify_freeze(root, freeze):
    for reference, digest in freeze["artifacts"].items():
        path = root / reference
        require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
                "frozen artifact escapes root")
        require(sha(path.read_bytes()) == digest, f"apparatus drift: {reference}")


def run_once(spec, config, output, transport=local_http):
    request_raw, prompt_raw = build_request(spec, config)
    # Exclusive marker precedes every network action. An interrupted call cannot be repeated.
    output.mkdir(parents=True, exist_ok=False)
    save(output / "request.json", request_raw)
    save(output / "prompt.txt", prompt_raw)
    started = now()
    receipt = {"started_at_utc": started, "request_sha256": sha(request_raw),
               "prompt_sha256": sha(prompt_raw), "model": config["model"],
               "model_digest": config["model_digest"],
               "provider_version": config["provider_version"],
               "parameters": config["options"], "generation_attempts": 0, "retries": 0,
               "tools": [], "session_reuse": False, "aperture": "exact request bytes",
               "hidden_provider_context": "UNKNOWN", "status": "APPARATUS_INVALID",
               "raw_response_sha256": None, "parsed_output_sha256": None, "errors": []}
    save_json(output / "before-send.json", receipt)
    parsed = None
    try:
        for endpoint, name in (("/api/version", "provider"), ("/api/tags", "models")):
            status, headers, raw, error = transport("GET", endpoint, timeout=10)
            save(output / f"{name}-discovery.raw.json", raw)
            receipt[name + "_discovery_sha256"] = sha(raw)
            require(status == 200 and error is None, "provider discovery failed")
            value = decoded(raw)
            if name == "provider":
                require(value["version"] == config["provider_version"], "provider version drift")
            else:
                model = next((m for m in value["models"] if m["name"] == config["model"]), None)
                require(model and model["digest"] == config["model_digest"], "model digest drift")
        receipt["generation_attempts"] = 1
        save_json(output / "send-started.json", {"at_utc": now(),
                                                "request_sha256": sha(request_raw),
                                                "generation_attempts": 1})
        status, headers, raw, error = transport("POST", "/api/generate", request_raw,
                                               config["timeout_seconds"])
        save(output / "provider-response.raw.json", raw)
        save_json(output / "http-response.json", {"status": status, "headers": headers,
                                                   "incomplete_read": error})
        receipt["raw_response_sha256"] = sha(raw)
        require(status == 200 and error is None, f"provider HTTP failure: {status}, {error}")
        value = decoded(raw)
        require(value.get("model") == config["model"], "response model mismatch")
        require(value.get("done") is True and value.get("done_reason") == "stop",
                "provider response incomplete or truncated")
        require("tool_calls" not in value and "tools" not in value, "tool response forbidden")
        save(output / "response-text.txt", value["response"].encode("utf-8"))
        parsed = decoded(value["response"])
        save_json(output / "parsed-output.json", parsed)
        receipt["parsed_output_sha256"] = sha((output / "parsed-output.json").read_bytes())
        errors = sorted(check_schema(spec["output_schema"]).iter_errors(parsed),
                        key=lambda e: str(e.path))
        require(not errors, "; ".join(f"{list(e.path)}: {e.message}" for e in errors[:12]))
        receipt["status"] = "PASS_REQUEST_PATH_ONLY"
    except Exception as error:
        receipt["errors"].append(f"{type(error).__name__}: {error}")
    receipt["finished_at_utc"] = now()
    save_json(output / "receipt.json", receipt)
    return receipt, parsed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        freeze = decoded(args.freeze.read_bytes())
        verify_freeze(args.root, freeze)
        for path in (args.spec, args.config):
            ref = path.resolve().relative_to(args.root.resolve()).as_posix()
            require(ref in freeze["artifacts"], "unfrozen request/configuration")
        receipt, _ = run_once(decoded(args.spec.read_bytes()), decoded(args.config.read_bytes()),
                              args.output)
        print(json.dumps(receipt, sort_keys=True))
        return 0 if receipt["status"] == "PASS_REQUEST_PATH_ONLY" else 1
    except Exception as error:
        print(f"APPARATUS_INVALID: {type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
