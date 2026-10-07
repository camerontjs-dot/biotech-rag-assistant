# Biotech local authoring v2: the canary was stopped by a resource guard after the provider accepted its schema

**Disposition: `RESOURCE_STOP_BEFORE_ANY_RESPONSE`.** Run `semantic-author-slot-bound-v2-20261007-attempt01`
is `APPARATUS_INVALID` at the canary. The provider's runner accepted the corrected schema and began
evaluating the 21,266-token prompt. About ten seconds after launch, the local supervisor's swap-growth
rule stopped the wrapper, before any output existed. There is no canary response, no author request
and no corpus; the corpus hash is `null`. The run is closed and is not retried or reused.

The stop leaves open whether the author boundary executes end to end. It does show that the provider
no longer refuses the schema at the construct that ended v1.

Source: v2 commit `f74cd88685b4f8f5a7d59b0460979c690a2028c3` (module SHA-256
`2085ece34c01ed117f5bcd0c9ab5cef88569b4e110a4dc1dc3bc680cebaf60c7`), published freeze
`d81ad3f733556e30e2bc7fbb1eeac0eb09c4a87b` (`EXECUTION-FREEZE.json` SHA-256
`35ac02945df4d086c914535357943558e14a9fb15a1b0774232edf78bb26cd25`), on branch
`research/semantic-author-slot-bound-v2-20261007`. It is based on PR #54's head
`9399e096185e8fc90d9026d97c1e715c750f2787`, whose reviewed files are byte-identical to
`513cf0629b20a8d876e161f32f8bc6c6549e2012`. Programme owner: issue #39.

## What the provider showed

Observed in the runner's own log for this call:

| | v1 canary (attempt01) | v2 canary (this run) |
| --- | --- | --- |
| Provider answer | HTTP 400 after 4.93 s: `schema must be an object` at `#/properties/rows/items` | none before the stop; HTTP 500 logged when the client connection closed at 9.72 s |
| Slot launched | no | yes (`processing task`) |
| Prompt tokens received | 0 | 21,266 |
| Prompt evaluation | none | started; steps at 0, 512 and 1,024 tokens logged; not completed |
| Tokens generated | 0 | 0 |

Inferred: the provider's JSON-schema conversion and grammar initialization accepted the v2 `format`
field, which carries all 18 schema keywords the author schemas use. v1's refusal came back as a 400
before any slot launch, and it came back in 4.93 s. This request was still running at 9.7 s and had
reached a slot. No other reading explains a refused schema getting that far, but no response was
seen, so this is an inference from log lines, not a result.

Not observed: any generated token, any grammar-constrained output, a stop reason, or a response body
to validate. The verbatim runner lines are in [TERMINAL.json](TERMINAL.json).

The prompt and the frozen output reserve fit the window: 21,266 + 6,144 = 27,410 tokens against 40,960.

## Why the call stopped

The supervisor aborts a call if swap grows by 256 MiB. At its first sample, 10.1 s after launch, swap
had grown 2,889.6 MiB (277.4 to 3,167.1 MiB), free memory read 24 percent and the pressure level was 2,
with `qwen3.5:9b` resident at 6.9 GB. It sent SIGTERM to the wrapper's process group and to nothing
else. The provider logged HTTP 500 for the closed connection.

The limit was wrong for this memory state. The v2 budget kept v1's 256 MiB swap-growth limit while
moving the two free-memory thresholds for today's state (54 to 58 percent free against v1's 78 to 80),
and the swap limit was not re-derived. Ollama's scheduler logged 5.6 GiB free and no free swap
immediately before the load, while `memory_pressure` read 57 percent free because it counts
reclaimable memory. Loading about 7 GiB of model weights and context against 5.6 GiB free made macOS page out about
2.9 GiB belonging to other applications. The supervisor did what the budget told it to. This is an error in the run's
apparatus, and it is the first thing the next attempt has to correct.

After the stop: no model resident, 63 percent free, pressure level 1, no wrapper or supervisor process.
Swap stayed near 3.1 GiB, which are other applications' pages that macOS returns lazily. No other
process was signalled.

## Counts

| Item | Count |
| --- | --- |
| Generation requests sent | 1 (canary, cancelled after 9.72 s) |
| Canary attempts / accepted | 1 / 0 |
| Responses received | 0 |
| Prompt tokens received by the runner / evaluation completed | 21,266 / no |
| Tokens generated | 0 |
| Retries | 0 |
| Author partitions planned / requested / accepted | 28 / 0 / 0 |
| Author partitions not attempted (sequence closed) | 28 |
| Cases / relations authored | 0 of 44 / 0 of 16 |
| `freeze-corpus` | NOT_RUN; precondition of 28 accepted partitions unmet |

Machine-readable record: [TERMINAL.json](TERMINAL.json).

## What this does not establish

- That the canary passes. It produced no output.
- That the 28 author schemas convert. They share the canary's keywords and constructs, but each is a
  different schema. Eighteen of the 28 need the exactly empty tuple, which the canary also contains.
- That constrained decoding honors the positional `const` assignments, or that `allOf` over a `$ref`
  does not repeat a property the definition already declares. The wrapper parses strictly and rejects
  duplicate keys, so a completed canary is the first place either would show.
- That a response fits the output reserve, or that the runner received untruncated context beyond its
  own `task.n_tokens` report. Context visibility stays `UNKNOWN` and semantic readiness `NOT_READY`.

## Offline evidence before the freeze

107 tests pass on Python 3.11, 3.12 and 3.13, locally and on hosted CI (run 37574355047: lint, the
frozen preparation validator and compilation executed alongside 107 tests in each Python job). They
repeat the v1 custody controls against the module that runs and add the schema-contract controls: the
gate in 25 schema positions, exact cardinality in all 28 author schemas, v1 and v2 rejecting the same
corruptions, canary keyword equality, frozen request bytes and the pre-send gate. Removing `maxItems`,
`minItems`, the positional `const`, the exactly empty tuple's cardinality, `prefixItems` or the gate
fails the relevant tests; all eight mutants are killed ([mutation check](schema_contract_mutation_check.py)).
None of this says anything about how the provider converts a schema. [OFFLINE-CHECKS.json](OFFLINE-CHECKS.json)
has the exit statuses and hashes.

## Still `NOT_RUN`

A/B/C adjudication, semantic assessor, reducer, heading grant #49, Biotech–CAL/EB integration. Wave B
remains `LOCKED`. BM25, the A07 negative result, the A08 bounded result, heading exclusion and the
TEST/PROSPECTIVE restrictions are unchanged. No merge or release. `main` is `cd9ba8bc…`; PR #54's head
is still `9399e096…`; v1 attempt01's evidence tip is still `bd9ba73a…`.

## Independence

Achieved: exact frozen request bytes, no tools, no session reuse, the freeze published before any
provider call, and the author role never reached. Unknown: hidden provider context, model training
independence, untruncated request context. The supervisor was a Claude Code session
(`claude-sonnet-5-5`) that had read the handoff, #39, PR #54's receipt and the module source.

## Deviations from the plan

- The branch is based on PR #54's head rather than the pinned source commit, to carry the handoff,
  CI workflow and review evidence. The three reviewed source files are byte-identical at both commits.
- The canary is wider than v1's by design: 18 keywords against 12, plus an exactly empty tuple.
- The budget moved two free-memory thresholds from v1's (start gate 60 to 50, abort floor 20 to 10),
  with the reason recorded in [budget.json](budget.json). The swap limits were kept, which is the
  error described above.
- Worktree under the project's `.worktrees` directory; virtual environment on Python 3.11.15;
  `caffeinate -i` during the call. The call lasted 13.2 s, so there is one mid-call resource sample.
- Raw supervisor logs and the provider-log window stay private; this directory carries path-projected
  logs and the extracted numbers. Only runner lines that belong to this request are quoted.

## Next evidence-producing boundary

A new run identity, `semantic-author-slot-bound-v2-20261007-attempt02`, with the same v2 source, the same
29 requests and the same runtime configuration, frozen and published before its canary. Only
`budget.json` needs to change, and the new freeze will show the request bytes by hash to be identical.
This run is not repaired, retried or reused.

The guard is a safety setting on the owner's machine, so its values are the owner's decision. The
smaller change is to keep the pressure-level, resident-size, context, battery and probe rules and replace
the 256 MiB swap-growth abort and the 768 MiB swap start gate with limits that detect thrashing rather
than a cold model load, for example an abort at 8 GiB of growth. That accepts a few GiB of paging per
load. The alternative is to free memory first so the provider sees about 8 GiB free at load, which
would let the tighter v1 limits stand.

## Evidence index

| File | Purpose |
| --- | --- |
| `TERMINAL.json` | Terminal record: timeline, observation, resource facts, denominators, identities |
| `budget.json`, `supervisor.py`, `supervisor_selftest.py` | Declared limits, enforcement, 21-test self-test (the supervisor differs from v1 by two lines) |
| `RUNTIME-PREFLIGHT.json`, `LOCAL-EXPOSURE-RECEIPT.json`, `OFFLINE-CHECKS.json`, `SUPERVISOR-FREEZE.json` | Prospective receipts, published before the call |
| `V1-TO-V2-CHANGES.json`, `v1-to-v2/` | What changed from v1, with diffs and hashes |
| `schema_contract_mutation_check.py` | Reproducible check that the schema-contract tests catch each mutant |
| `offline/`, `run-logs-public/` | Logs with local prefixes replaced; each `PROJECTION-MAP.json` records original and published hashes |
| `../semantic-author-slot-bound-v2-20261007-attempt01/` | Frozen packet and the partial canary call (the full model inventory is hash-only) |
