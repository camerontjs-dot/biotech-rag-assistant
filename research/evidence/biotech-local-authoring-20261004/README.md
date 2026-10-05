# Biotech local authoring task: first durable blocker at the canary

**Disposition: `FIRST_DURABLE_BLOCKER`.** Run `semantic-author-slot-bound-v1-20261004-attempt01` is
`APPARATUS_INVALID` at the canary. **No corpus freeze exists.** The corpus hash is `null`.

Source: published `513cf0629b20a8d876e161f32f8bc6c6549e2012`, tree
`6428495c4f3b373cd07bdebcc7916834c157da3f`, boundary module SHA-256
`74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450`. Instructions were read from the
PR #54 head `9399e096185e8fc90d9026d97c1e715c750f2787`. Programme owner: issue #39.

## What happened

1. **Offline checks, exit statuses preserved.** The documented suite ran 53 tests, all OK, exit 0.
   The frozen preparation validator returned `PASS_PREPARATION_STRUCTURE_ONLY` (31 artifact hash
   checks, 6 launch packets, 0 semantic invocations). `prepare` and `verify` exited 0
   (`PASS_PROSPECTIVE_PLAN_ONLY`: 28 partitions, 44 cases, 16 relations, 0 provider calls).
   See [OFFLINE-CHECKS.json](OFFLINE-CHECKS.json). These are token and fake-HTTP checks.
2. **Runtime inventory.** Ollama 0.35.1, `qwen3.5:9b`, digest
   `6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`. No model was resident and no
   client had sent a generation request since the task began (provider log). Apple M3, 24 GiB
   unified memory, on battery power at 100%. See [RUNTIME-PREFLIGHT.json](RUNTIME-PREFLIGHT.json).
   Declared budget: `num_ctx` 40,960, `num_predict` 6,144, timeout 1,800 s, with memory, pressure,
   swap and power limits. See [budget.json](budget.json). The full model inventory stays local
   (hash-only).
3. **Prospective freeze published first.** Commit
   `9ba158e50b9c9d75503dbc5c946e8271c890c8ea` (2026-10-05T01:06:06Z) carries the configuration,
   plan, 28 requests, canary, `EXECUTION-FREEZE.json`, budget, supervisor and receipts. All 53
   published blobs were read back from GitHub and matched. Zero provider requests preceded it.
4. **Canary.** One request, sent at 01:06:52Z through the frozen wrapper under the local
   supervisor. The provider answered **HTTP 400 after 4.93 s**:

   > Field 'json_schema': "json_schema": JSON schema conversion failed:
   > JSON schema error at #/properties/rows/items: schema must be an object

   The runner had started (`n_ctx` 40,960, KV buffer 1,280 MiB) but evaluated **no prompt tokens and
   generated none**. The wrapper wrote `APPARATUS_INVALID` and exited 1. The supervisor stopped the
   sequence. No author request was sent and nothing was retried.

## What this does and does not show

- The location the provider named is the canary schema's only `items: false`, a boolean subschema
  used to close the `prefixItems` tuple. The 53 hosted tests validate with a JSON Schema validator
  and fake HTTP, so they could not reveal this. PR #54 listed provider formatter compatibility as
  not established; this is the first real-provider evidence and it is negative.
- An offline walk of the frozen schemas ([SCHEMA-FEATURE-SURVEY.json](SCHEMA-FEATURE-SURVEY.json))
  finds the same construct three times in **each** of the 28 author schemas. They would be expected
  to be refused the same way. That is an inference: no author request was sent, by design.
- The converter stops at its first error. Provider handling of `prefixItems`, `allOf`, `const`,
  `$ref`/`$defs` and `additionalProperties: false` in these schemas is **untested**.
- This is not a resource, timeout, truncation or semantic outcome. No authored text exists, so
  context visibility stays `UNKNOWN`, semantic readiness `NOT_READY`, validity `NOT_ASSESSED`.

## Denominators

| Item | Count |
| --- | --- |
| Provider requests sent | 1 (canary, HTTP 400) |
| Canary attempts / accepted | 1 / 0 |
| Prompt tokens evaluated / tokens generated | 0 / 0 |
| Retries | 0 |
| Author partitions planned / requested / accepted / invalid | 28 / 0 / 0 / 0 |
| Author partitions not attempted (sequence closed) | 28 |
| Cases planned / authored | 44 / 0 |
| Relations planned / authored | 16 / 0 |
| `freeze-corpus` | NOT_RUN; precondition of 28 accepted partitions unmet |

Machine-readable record: [TERMINAL.json](TERMINAL.json).

## Still `NOT_RUN`

A/B/C adjudication, semantic assessor, reducer, heading grant #49, Biotech–CAL/EB integration.
Wave B remains `LOCKED`. BM25, the A07 negative result, the A08 bounded result, heading exclusion and
the TEST/PROSPECTIVE restrictions are unchanged. No merge or release. PR #54's head is unchanged.

## Independence

Achieved: exact frozen request bytes, no tools, no session reuse, freeze published before any
provider call, and the author role was never reached. Unknown: hidden provider context, model
training independence, untruncated request context.

## Deviations from the handoff plan

- Worktree placed under the project's `.worktrees` directory rather than the plan's sibling path.
- Python 3.11.15 for the virtual environment (default `python3` is 3.14.4; 3.11 is in the hosted matrix).
  `PYTHONDONTWRITEBYTECODE=1` set; the validator receipt was written outside `/tmp`.
- A local resource supervisor, budget and 21-test self-test were added and published in the freeze
  commit. The wrapper ran exactly the protocol's `canary` command through it. The call lasted 9.1 s,
  shorter than the supervisor's 10 s sample interval, so there is no mid-call resource sample.
- `caffeinate -i` kept the machine awake because it was on battery power.
- Only numeric metrics from the earlier run (token counts, durations, memory) informed sizing. No
  earlier authored text was read.
- EB's repository and processes were inspected read-only. None was modified, stopped or signalled.

## Next evidence-producing action

A separately identified successor must remove boolean subschemas from the provider-facing output
schema contract, add an offline gate that rejects them, and be qualified before a new local run. It
needs a new run directory, a new frozen configuration and freeze, and a provider-conversion canary
frozen before use. This attempt is not repaired, retried or reused.

## Evidence index

| File | Purpose |
| --- | --- |
| `TERMINAL.json`, `SCHEMA-FEATURE-SURVEY.json` | Terminal record and offline schema survey |
| `budget.json`, `supervisor.py`, `supervisor_selftest.py` | Declared limits, enforcement, 21-test self-test |
| `RUNTIME-PREFLIGHT.json`, `LOCAL-EXPOSURE-RECEIPT.json`, `OFFLINE-CHECKS.json`, `SUPERVISOR-FREEZE.json` | Prospective receipts |
| `offline/`, `run-logs-public/` | Logs with local prefixes replaced; `PROJECTION-MAP.json` records original and published hashes |
| `../semantic-author-slot-bound-v1-20261004-attempt01/calls/canary/` | Raw canary request, response and receipts (the full model inventory is hash-only) |
