# Prospective semantic author slot boundary v2

Work class: research infrastructure. v2 keeps the v1 author assignment boundary and
changes the schema contract the provider converts. The first real-provider canary of v1
(`semantic-author-slot-bound-v1-20261004-attempt01`) was refused by Ollama 0.35.1 with
HTTP 400 before any prompt token was evaluated: `JSON schema error at
#/properties/rows/items: schema must be an object`. The refused construct is the boolean
subschema `items: false`, which v1 used to close every `prefixItems` tuple. It appears
three times in each of the 28 author schemas and once in the canary.

v2 closes each tuple with exact cardinality instead, rejects any remaining boolean
subschema offline before a request can be built or sent, freezes the exact provider
requests before any send, and widens the canary to every schema keyword the 28 author
schemas use. It does not qualify semantic judgments, run an assessor, or change the
product.

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
The regression reproduces that slot vector with uninterpreted test tokens only.

The v1 boundary (module SHA-256 `74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450`,
source `513cf0629b20a8d876e161f32f8bc6c6549e2012`) ran its canary once and was refused
by the provider's schema converter: one request, zero author requests, no corpus. That
run directory and its evidence on `local/biotech-authoring-20261004` (tip
`bd9ba73a1310564ba40bbb8007da0fe8a333e54c`) stay as terminal `APPARATUS_INVALID` evidence.
Nothing in it is repaired, retried, reused or relabeled. This wrapper accepts only the
new `research/evidence/semantic-author-slot-bound-v2-*` namespace, so a v1 run directory
cannot be continued or verified as v2.

## Provider schema contract

**Tuples.** `minItems == maxItems == len(prefixItems)` already forbids any extra member, so
the boolean `items: false` adds no constraint. v2 drops it:

| Construct | v1 | v2 |
| --- | --- | --- |
| Non-empty tuple | `minItems = maxItems = n`, `prefixItems` of `n`, `items: false` | the same without `items` |
| Exactly empty tuple | `minItems = maxItems = 0`, `items: false` | the same without `items` |
| Each author schema | 3 boolean `items` | none |

Every other byte of the 28 author schemas, the request instruction, the artifacts and the
assignments is unchanged. The schema stays valid Draft 2020-12 and is still checked by the
frozen `jsonschema` backend. The tests assert that each v2 author schema equals its v1
schema minus exactly those `items` values, and that v1 and v2 reject the same corruptions:
a missing or extra row, a reordered or wrong positional slot, a wrong `const` assignment, a
non-empty array where an array must stay empty. Dropping `maxItems` or `minItems` from the
tuple builder fails those tests, which is what makes the removal safe rather than assumed.

**Gate.** `boolean_subschemas` walks the JSON Schema 2020-12 vocabulary by position, so a
property that is merely named like a keyword is not mistaken for one. A value that must be a
schema is rejected when it is a boolean or any other non-object: `items`, `prefixItems`
members, `properties` and `$defs` values, `allOf`/`anyOf`/`oneOf` members, `not`,
`if`/`then`/`else`, `contains`, `propertyNames`, `additionalItems`, `unevaluated*`,
`patternProperties`, `dependentSchemas`, and `additionalProperties` unless it is `false`. A
boolean under a keyword the gate cannot classify is rejected. `const`, `enum`, `default`,
`examples`, `required`, `type` and the `uniqueItems` flag are data or flags, not subschemas.
`additionalProperties: false` is the one declared native flag form: the frozen author
schemas need it, and only the real-provider canary shows how the provider treats it.

The gate runs at three points: when each author schema and the canary are constructed;
in `prepare` and `verify` over all 29 schemas, recorded as `provider_schema_gate` in
`PLAN.json`; and immediately before every send over the `format` field of the exact
request bytes.

**Frozen requests.** `prepare` writes the exact request and prompt bytes of the canary and
all 28 author calls under `generated/` and adds them to `EXECUTION-FREEZE.json`. `verify`
rebuilds them from the frozen specs and configuration and compares bytes. Before each send
the wrapper rebuilds the request again and requires equality with the frozen file. `PLAN.json`
records every request hash.

**Canary.** It uses the same `tuple_schema` builder and the same embedded probe as v1: the
largest author prompt by UTF-8 byte count, as uninterpreted data. v1's canary used 12 of the
18 schema keywords the author schemas use. v2's uses exactly those 18 (`$defs`, `$ref`,
`$schema`, `additionalProperties`, `allOf`, `anyOf`, `const`, `enum`, `items`, `maxItems`,
`minItems`, `minLength`, `prefixItems`, `properties`, `required`, `title`, `type`,
`uniqueItems`), in their authoring constructs: a `$defs` row with a nested `$schema` and a
`title`, a tuple whose `allOf` pins `const` values over properties the row definition also
declares, a nullable `anyOf`, an `enum`, a unique bounded array, an unbounded array of
objects, and an exactly empty tuple. `prepare` and `verify` fail if the canary's keyword set
differs from the author schemas' in either direction. Its output is fixed (`CANARY_OUTPUT`)
and carries no semantic content.

A passing canary shows that the provider converted these constructs and returned a
schema-valid result. It does not show that each of the 28 author schemas converts or that
decoding stays inside the output reserve. A conversion or decoding failure on any later call
is terminal for the run. The converter stops at its first error, so only a real-provider
call shows how `prefixItems`, `allOf` with `const`, `$ref` and the other keywords are handled.

## Boundary and acceptance

Before any provider action, verify the pinned inherited artifacts, all 28 exact
components, 44 case/design slots, 16 relations, complete order/membership and globally
unique opaque identities. Bind the executing module and its inherited imports to the
source bytes under the declared root; reject symlinked run ancestors or members before
any network activity. Generate compact Draft 2020-12 schemas using local `$defs`,
`$ref`, `prefixItems`, `allOf` and per-position `const` constraints. The schema adds
explicit `left_slot`/`right_slot` assignments at author transport; materialization
replaces them with the already frozen endpoint UUIDs. Sealed design and relations
remain separate from input-only cases.

The design fixes each anchor's role, category and seed kind, and each variant's role
and category. It does **not** assign a particular seed kind to every variant; the
three existing enum values remain legal. Relation IDs, order, family, mode and both
endpoints are fixed by the recipe. No semantic field is inferred or repaired.

A request's inherited `PASS_REQUEST_PATH_ONLY` receipt is only transport/schema
acceptance. The wrapper writes `PASS_AUTHOR_PARTITION_STRUCTURE_ONLY` only after
slot assignments, exact unique text anchors, code-point offsets, source hashes, word
limits, frozen endpoint identities and declared changed-text references validate.
Changed-text occurrence checks establish reference validity only: they do not prove
complete edit accounting, meaningful alignment, semantic invariance or mutation.

Before the next request, the wrapper verifies the prospective freeze and reconstructs
all earlier acceptance from request/raw-response/parsed-output custody. Persisted
materialized bytes must match their receipt hash **and** a canonical rederivation
from the unchanged raw response, before any next request or complete-corpus freeze.
The boundary receipt hashes all 11 captured transport artifacts, including response
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
Only the new `research/evidence/semantic-author-slot-bound-v2-*` namespace is accepted.

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
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_author_slot_boundary_v2.py' -v
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_author_slot_boundary_v1.py' -v
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_request_once.py' -v
PYTHONPATH=src:research python -m unittest discover -s research -p 'test_semantic_assessor_preparation.py' -v
```

The v2 test module repeats the v1 custody controls against the module that actually runs,
then adds the schema-contract controls above: the gate in every schema position, exact
cardinality in all 28 author schemas, v1/v2 verdict equality over every corruption,
canary keyword coverage, frozen request bytes, and the pre-send gate. Tests use
uninterpreted tokens, temporary directories and fake HTTP. A 44-row synthetic fixture
proves structural acceptance only. Corruptions retain valid counts/enum values while
violating assignments, order, references or custody; failures must remain failures.
No offline check says anything about how the provider converts a schema. The implementing
and reviewing agents have historical failure context. This is an engineering check, with no
clean-room or semantic-independence claim.

## Local preflight, prospective freeze and fresh execution

Use a new isolated worktree at the published successor SHA. Review live coordination
issue #39 before execution. Verify the exact preserved authority identities and pass
the offline suite. Do not reuse any old calls, runtime directory or corpus attempt.

1. Inspect the actual local provider and model inventory. Select and record the exact
   model name, 64-hex digest, provider version, generation options and finite timeout.
   Both `num_ctx` and `num_predict` must be explicit. The command has **no inherited
   model default**. A successor to a refused provider call keeps the model, digest,
   provider version and generation options of the refused run unless the live runtime no
   longer supports them: a schema refusal is not evidence for tuning any of them. Preserve
   the local memory/resource preflight and runtime receipt.
2. Prepare a fresh JSON config with exactly `model`, `model_digest`, `provider_version`,
   `options`, `timeout_seconds`. Options use the frozen runner's allowlist. Run the
   following commands after replacing `RUN` and the config path with the new identities.

```sh
RUN="$PWD/research/evidence/semantic-author-slot-bound-v2-YYYYMMDD-attempt01"
python research/semantic_author_slot_boundary_v2.py prepare --root "$PWD" --run-dir "$RUN" --config /path/to/new-local-runtime-config.json
python research/semantic_author_slot_boundary_v2.py verify --root "$PWD" --run-dir "$RUN"
```

3. Inspect the complete generated packet and commit/publish its `PLAN.json`, 28 request
   specs, the exact generated requests, canary, runtime config and `EXECUTION-FREEZE.json`
   **before any new provider call**. Preserve the exact freeze commit/hash and separate
   local exposure/configuration receipts. All prospective call counts remain zero and the
   corpus hash null at this point. The full byte/hash freeze is rechecked before every
   wrapper call.
4. Run the mandatory nonsemantic feature/capacity canary. It exercises the schema
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
   A provider refusal of the canary schema is terminal for the run: preserve the exact
   provider error and classify the refused construct without sending any author request.

```sh
python research/semantic_author_slot_boundary_v2.py canary --root "$PWD" --run-dir "$RUN"
```

5. On accepted canary, execute `author-01` through `author-28` strictly in that order.
   The custodian launches the stateless no-tool HTTP wrapper. The author receives only
   the frozen allowlist embedded in each request, never this supervisor protocol,
   history, broad conversation, earlier model output or sealed peer material. Preserve
   stdout/stderr and actual process exit status for each command; stop on the first
   nonzero exit. A timeout/interruption is not permission to repeat the call.

```sh
python research/semantic_author_slot_boundary_v2.py run --root "$PWD" --run-dir "$RUN" --group author-01
```

Repeat that exact action for the next frozen group only after the preceding process
has completed and its `author-boundary.json` contains the accepted partition status.
The wrapper rejects skipping, reusing, or continuing past a failed call.

6. After all 28 accepted calls, preserve a full corpus-freeze attempt log and run:

```sh
python research/semantic_author_slot_boundary_v2.py freeze-corpus --root "$PWD" --run-dir "$RUN"
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
