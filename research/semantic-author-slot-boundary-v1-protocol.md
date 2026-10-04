# Prospective semantic author slot boundary v1

Work class: research infrastructure. This successor checks frozen author assignments
before accepting each response and before freezing a complete corpus. It does not
qualify semantic judgments, run an assessor, or change the product.

## Authority and failure addressed

The unchanged semantic/design authority is [PR #30](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/30)
at `d1e092b7cdb878d064735d597e8c3b2d6c710157`. Its frozen 44-slot design remains
`case-design.json` SHA-256 `b19a716ee490e4aa3d2509b9bc7e7eae3186390a267f32b8dbd063b62539f1dd`;
the rubric remains `11092f20ec28a1124b208f4eb09d43258c125fe4e57b94692613fa8ad009359d`.
The unchanged partition and opaque identities come from [PR #38](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/38)
at `1e3d79a53f181c79bdeeb6137e88ae2897797106`; its apparatus freeze SHA-256 is
`a69fb2f59617159e75f75568343993c27b3bf67e8b5460ca8cc8cccb782d9343`.

[PR #51](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/51), terminal head
`7556badf6077bac2edd20f163faa5af0ef1b95d1`, retained 44 returned case rows containing
33 unique slots, 11 missing slots and 11 duplicate occurrences. Its root slot proof
identifies six case-assignment mismatches. Generic request schemas constrained lengths,
not per-partition assignments. The rejected outputs and all inherited files remain
historical evidence. No output is repaired, relabeled or imported into a new corpus.
The new regression reproduces that slot vector with uninterpreted test tokens only.

## Boundary and acceptance

Before any provider action, verify the pinned inherited artifacts, all 28 exact
components, 44 case/design slots, 16 relations, complete order/membership and globally
unique opaque identities. Bind the executing module and its inherited imports to the
source bytes under the declared root; reject symlinked run ancestors or members before
any network activity. Generate compact Draft 2020-12 schemas using local `$defs`,
`$ref`, `prefixItems`, `allOf` and per-position `const` constraints. The new schema adds
explicit `left_slot`/`right_slot` assignments at author transport; materialization
replaces them with the already frozen endpoint UUIDs. Sealed design and relations
remain separate from input-only cases.

The design fixes each anchor's role, category and seed kind, and each variant's role
and category. It does **not** assign a particular seed kind to every variant; the
three existing enum values remain legal. Relation IDs, order, family, mode and both
endpoints are fixed by the recipe. No semantic field is inferred or repaired.

A request's inherited `PASS_REQUEST_PATH_ONLY` receipt is only transport/schema
acceptance. The new wrapper writes `PASS_AUTHOR_PARTITION_STRUCTURE_ONLY` only after
slot assignments, exact unique text anchors, code-point offsets, source hashes, word
limits, frozen endpoint identities and declared changed-text references validate.
Changed-text occurrence checks establish reference validity only: they do not prove
complete edit accounting, meaningful alignment, semantic invariance or mutation.

Before the next request, the wrapper verifies the prospective freeze and reconstructs
all earlier acceptance from request/raw-response/parsed-output custody. Persisted
materialized bytes must match their receipt hash **and** a canonical rederivation
from the unchanged raw response, before any next request or complete-corpus freeze.
The v2 boundary receipt hashes all 11 captured transport artifacts, including response
text, both discovery responses, before-send/send-started markers and HTTP metadata.
Their retained content is checked against the frozen request and runtime configuration;
marker identities and UTC chronology must agree. Boundary stage, request identity,
errors and semantic/adjudication states must match their bounded meanings. Final corpus
commitments include the mandatory canary acceptance as well as every author receipt.
These are retained-evidence consistency checks; they do not authenticate the provider
against coordinated rewriting of all inputs, receipts and source authority.
A missing,
interrupted, invalid or out-of-order call stops the sequence. One generation attempt
per frozen call; no retries, repair, adaptive repartition or continuation after failure.
Only the new `research/evidence/semantic-author-slot-bound-v1-*` namespace is accepted.

The final command reconstructs all 28 drafts from raw accepted calls and validates
the full frozen corpus contract, including declared guard coverage. It writes no
corpus files before the complete corpus passes. Its result is
`PASS_COMPLETE_CORPUS_STRUCTURE_ONLY`. Privacy, synthetic provenance and historical
separation still require the frozen custodian review. Author hypotheses and declared
guard opportunities remain hypotheses. A/B/C, semantic assessor and reducer remain
`NOT_RUN`; the local authoring task stops here.

The corpus-freeze command writes an exclusive attempt marker and a separate result
receipt. An incomplete corpus or interruption cannot be retried under the same run.
The wrapper closes the author sequence once that freeze attempt begins.

## Offline qualification

From the repository root, with the pinned dependency environment:

```sh
python -m pip install -r research/semantic-assessor-preparation-requirements.txt
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_author_slot_boundary_v1.py' -v
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_request_once.py' -v
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_assessor_preparation.py' -v
```

Tests use uninterpreted tokens, temporary directories and fake HTTP. A 44-row synthetic
fixture proves structural acceptance only. Corruptions retain valid counts/enum values
while violating assignments, order, references or custody; failures must remain failures.
The implementing and reviewing agents have historical failure context. This is an
engineering check, with no clean-room or semantic-independence claim.

## Local preflight, prospective freeze and fresh execution

Use a new isolated worktree at the published successor SHA. Review live coordination
issue #39 before execution. Verify the exact preserved authority identities and pass
the offline suite. Do not reuse any old calls, runtime directory or corpus attempt.

1. Inspect the actual local provider and model inventory. Select and record the exact
   model name, 64-hex digest, provider version, generation options and finite timeout.
   Both `num_ctx` and `num_predict` must be explicit. The command has **no inherited
   model default**. Historical qwen3-coder:30b and qwen3.5:9b settings are not current
   capacity evidence. Preserve the local memory/resource preflight and runtime receipt.
2. Prepare a fresh JSON config with exactly `model`, `model_digest`, `provider_version`,
   `options`, `timeout_seconds`. Options use the frozen runner's allowlist. Run the
   following commands after replacing `RUN` and the config path with the new identities.

```sh
RUN="$PWD/research/evidence/semantic-author-slot-bound-v1-YYYYMMDD-attempt01"
python research/semantic_author_slot_boundary_v1.py prepare --root "$PWD" --run-dir "$RUN" --config /path/to/new-local-runtime-config.json
python research/semantic_author_slot_boundary_v1.py verify --root "$PWD" --run-dir "$RUN"
```

3. Inspect the complete generated packet and commit/publish its `PLAN.json`, 28 request
   specs, canary, new runtime config and `EXECUTION-FREEZE.json` **before any new provider
   call**. Preserve the exact freeze commit/hash and separate local exposure/configuration
   receipts. All prospective call counts remain zero and corpus hash null at this point.
   The full byte/hash freeze is rechecked before every wrapper call.
4. Run the mandatory nonsemantic feature/capacity canary. It exercises the new schema
   mechanisms against the actual provider and embeds the largest author prompt by
   UTF-8 byte count as uninterpreted data. It must return a complete valid token result
   and report `prompt_eval_count` with room for the frozen `num_predict` reserve.
   Record memory behavior, prompt tokens and response completion. Largest byte count
   does not prove largest token count, and one schema success does not prove general
   formatter support. Each actual author response must also fit the pinned reserve.
   A reported `prompt_eval_count` within that reserve does **not** prove the provider
   consumed an untruncated request: a server may truncate first and report the smaller
   count. Preserve separate local evidence of untruncated actual request/token-budget
   handling before semantic use. If the runtime cannot expose that evidence, retain
   context visibility as `UNKNOWN` and semantic readiness as `NOT_READY`. This wrapper
   deliberately emits that limitation even after a structural corpus pass. It does
   not monitor local memory pressure; the local supervisor must record and enforce
   the separately declared resource budget and stop on unsafe capacity behavior.
   Do not increase the window, change model/schema/options or retry after a failure;
   preserve a terminal apparatus-invalid result and prepare a new successor if needed.

```sh
python research/semantic_author_slot_boundary_v1.py canary --root "$PWD" --run-dir "$RUN"
```

5. On accepted canary, execute `author-01` through `author-28` strictly in that order.
   The custodian launches the stateless no-tool HTTP wrapper. The author receives only
   the frozen allowlist embedded in each request, never this supervisor protocol,
   history, broad conversation, earlier model output or sealed peer material. Preserve
   stdout/stderr and actual process exit status for each command; stop on the first
   nonzero exit. A timeout/interruption is not permission to repeat the call.

```sh
python research/semantic_author_slot_boundary_v1.py run --root "$PWD" --run-dir "$RUN" --group author-01
```

Repeat that exact action for the next frozen group only after the preceding process
has completed and its `author-boundary.json` contains the accepted partition status.
The wrapper rejects skipping, reusing, or continuing past a failed call.

6. After all 28 accepted calls, preserve a full corpus-freeze attempt log and run:

```sh
python research/semantic_author_slot_boundary_v1.py freeze-corpus --root "$PWD" --run-dir "$RUN"
```

Record complete input-only case, sealed design and relation bytes/hashes, all call
receipts and the first outcome. Perform and record the custodian's privacy/provenance/
historical-copy check without revealing history to the author. Publish the bounded
result and stop before A/B, assessor, reducer, Wave B, CAL integration, promotion,
merge or release. A valid corpus enables a separately authorized adjudication packet;
it does not qualify the semantic assessor by itself.

## Current execution state

New provider authoring, semantic corpus, A/B/C, semantic assessor and reducer: **NOT_RUN**.
Offline token fixtures and fake transport are never counted as semantic execution.
