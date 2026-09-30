# Slice 5D — schema-constrained Ollama Wave A successor

Status: preregistered before any successor live-model call.

## Objective

Repeat Wave A as a separately identified live-generation successor that reaches the deterministic
G2-G7 boundary instead of failing solely because the provider wrapped JSON in Markdown fences.

This is exploratory DEV/shadow evidence. It cannot promote public generation.

## Frozen predecessors

Boundary pressure-test predecessor:
- PR #14
- qualified head: `0721097129c29c375f8521cfa044d5268e337138`
- disposition: `PASS_GENERATION_BOUNDARY_PRESSURE_TEST_V1`

First live Wave A predecessor:
- original bundle head:
  `a7d2e69cd8ebbee2e0d66a596a39db7334fb43a5`
- model: `gemma3:12b`
- model digest:
  `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a`
- 6 callable cases, 6 model calls, 0 retries
- replay: all six callable responses failed G1 because exact Markdown-fenced responses were
  preserved as strings.

The first run remains valid evidence and is not rewritten.

## Successor changes

The successor changes exactly these material layers:

1. deterministic boundary hardening inherited from PR #14:
   - packet-id integrity verification before generation;
   - exact quantity-atom comparison;
   - case-robust controlled-identifier grounding;
2. schema-constrained provider transport using Ollama's `format` request field.

The textual model prompt remains byte-identical to the first run.

## Live model identity

Use exactly:
- provider/runtime: local Ollama;
- model: `gemma3:12b`;
- required digest:
  `f4031aab637d1ffa37b42570452ae0e4fad0314754d17ded67322e4b95836f8a`.

If the installed digest differs, stop before any generation call.

## Frozen generation parameters

- temperature: 0
- seed: 42
- num_ctx: 32768
- num_predict: 4096
- top_k: 40
- top_p: 1.0
- min_p: 0.0
- repeat_penalty: 1.0
- stream: false
- raw: true
- keep_alive: 0

One request per callable case. No retry.

## Structured-output transport

Every request supplies exactly:
- model ID;
- frozen prompt + canonical serialized EvidencePacket;
- `GeneratedAnswer.model_json_schema()` as the Ollama `format` value;
- the frozen options above.

The adapter uses no tools, retriever, corpus handle or web surface.

If the provider response field still is not valid JSON, preserve it as a string and let G1 reject it.
Do not strip fences or repair syntax.

## Wave A aperture

Use the qualified successor bundle exported from the exact PR head.

Wave A:
- 9 total cases;
- 6 callable cases;
- empty-packet cases are not sent to Ollama.

Wave B remains locked. The runner reads:
- manifest.json
- prompt.txt
- wave-a-probes.jsonl

It does not read or hash Wave B.

## Raw preservation

For every model call preserve:
- exact raw HTTP response body;
- provider response envelope;
- parsed `response` JSON value when valid, otherwise exact response string.

Write:
- `outputs.jsonl`
- `run_metadata.json`
- `raw-manifest.json`
- per-case raw provider response files.

## Replay

After all six model calls are frozen, replay `outputs.jsonl` through the exact repository G1-G7
engine at the same successor head with `--wave a`.

No generation call occurs during replay.

## Exploratory interpretation

Primary questions for this successor:
- does schema-constrained transport eliminate the predecessor's G1-only formatting failure?
- which real outputs now reach G2-G7?
- which accepted claims survive deterministic gates?
- do the four near-miss probes resolve as `not_stated`?
- do the two supported controls reach `generated` without unsupported material claims?

Human review is required for every accepted claim. No semantic-support metric is frozen here.

## Stop rule

After one live Wave A execution and one deterministic replay:
- preserve all raw and gated results;
- do not retune and rerun under the same identity;
- classify remaining failure types;
- decide whether the rubric/apparatus is ready for Wave B DEV.

TEST and PROSPECTIVE remain untouched.
