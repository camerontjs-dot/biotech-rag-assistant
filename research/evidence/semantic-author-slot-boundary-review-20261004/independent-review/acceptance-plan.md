# Separate engineering boundary review: frozen baseline and successor probes

## Scope and status

Prepared before reading any new successor implementation. The reviewed framework is Git commit `1e3d79a53f181c79bdeeb6137e88ae2897797106` in `<scratch>/biotech-authoring`. The failed-corpus record is Git object `7556badf6077bac2edd20f163faa5af0ef1b95d1`. All historical reads use exact Git objects; the author worktree remains untouched. No provider calls, network lookups, GitHub writes, semantic adjudication, or product changes are part of this review.

This is ordinary separate-context engineering review. It is not blind semantic adjudication, a human agreement estimate, or evidence of independent model training. Synthetic test fixtures use uninterpreted tokens and never become a candidate semantic corpus. The successor implementation is pending exact-commit review.

## Governing source and reproduced observations

The frozen semantic protocol requires 44 packets: 28 anchors, eight invariance variants, and eight mutations, with sealed design and 16 endpoint relations. The construction remains author hypotheses until adjudication. A local corpus freeze must leave A/B/C, assessor implementation, qualification, and accepted expectations unexecuted. Incomplete authoring does not earn a corpus freeze.

The principal sources at the frozen commit are:

- `research/evidence/qualifier-grounding-semantic-assessor-controls-v1/case-construction.md`: exact inventory, opaque identities, separation of cases from sealed design, no semantic repair, full-fragment custody, mechanical source spans, and authoring failure boundary.
- `research/evidence/qualifier-grounding-semantic-assessor-controls-v1/case-design.json`: ordered 44-slot inventory, categories, roles, anchor seed kinds, variant recipes, and relation families/modes.
- `research/evidence/qualifier-grounding-semantic-assessor-controls-v1/schemas/{case,author-design,relations}.schema.json`: neutral input shape, body/distractor cardinalities, structural declarations, and relation maps.
- `research/build_semantic_author_requests.py`: transport schema construction, partition preparation, mechanical materialization, and final assembly.
- `research/check_semantic_assessor_preparation.py`: inherited case and corpus structural gate.
- `research/run_semantic_request_once.py`: strict JSON, exact request serialization, frozen configuration checks, exclusive output creation, captured raw response, and zero retries within one call.
- `research/evidence/semantic-adjudication-request-bound-v2/{README.md,author-partition.json,APPARATUS-FREEZE.json}`: immutable 28-partition execution plan, frozen ID assignment, request/configuration authority, and stop-on-invalidity declaration.

The historical plan has 28 partitions, 44 unique slots, 16 relations, and 528 reserved unique IDs: one case ID, four witness/source ID pairs, and three distractor IDs per slot. Actual packets may use only a prefix of the reserved body and distractor positions. A fresh successor may prepare fresh identities before execution, but the resulting assignment must be frozen, globally unique, and stable throughout that run.

The baseline transport schema fixes array lengths but accepts arbitrary strings for `cases[*].slot` and broad strings for design slots and relation IDs. Materialization subsequently enforces case list equality but only set equality for design and relation identifiers. Categories, roles, seed kinds, family/mode binding, and aggregate guard coverage are stronger downstream corpus checks. The historical standalone assembler reads `author-materialized` files and validates their content without checking their origin against raw provider responses. A successor wrapper must not mistake that helper's success for a complete custody gate.

The failure record at `research/evidence/semantic-control-memory-bounded-20261003/corpus-freeze-20261004/` preserves a transport success and a distinct corpus failure. It records 28 complete schema-valid responses and 44 case rows, but only 33 unique planned case slots. Eleven variant/mutation slots are missing; ten partitions fail the unchanged materializer. Six fail case slot/order, one fails design assignment, and three first fail relation assignment. The full identifier cross-check finds that none of the 16 returned relation IDs matches a required relation-slot ID. These are structural findings, not judgments about the text's semantic correctness.

A separate historical identifier/custody pass reports 44 design rows, 38 unique design identifiers, 37 unique planned design slots, seven missing planned design slots, six duplicated anchor identifiers, and one unexpected identifier (`mutation_ case_id`). It enumerated 301 attempt artifacts, 31 request directories, 30 raw responses, and 28 parsed outputs, and checked 118 request/prompt/raw/parsed receipt hashes plus 28 raw-to-text-to-parsed chains without a mismatch. Custody attacks below are prospective adversarial tests, not allegations of historical tampering.

`frozen_baseline_probe.py` provides a no-network reproduction against exact historical source with `jsonschema==4.25.1`. It checks schema-valid identifier and ordering mutations and demonstrates the historical assembler's lack of a raw-origin gate using structurally valid uninterpreted fixtures. Its generated staging trees are temporary and removed. Its result is explicitly not an authored corpus or a semantic result.

## Twelve acceptance probes for the successor

Each negative probe starts from a valid structural token fixture and changes one relevant dimension. Prefer a real frozen request schema plus the production wrapper and a recording fake transport. A helper-only rejection is insufficient if the production sequence can still proceed. Every failing post-send probe must preserve the response and leave no accepted full corpus. Every failing preflight probe must make zero network calls, including discovery calls.

### BR-01 — Exact case slots and position

For a multi-slot partition, replace a required slot with an already present slot while retaining array length; substitute another valid inventory slot from a different partition; swap two rows; omit or append a row. In the largest partition, use the historical pattern `anchor_01` through `anchor_07` in place of its actual anchor/variant/mutation assignment. The transmitted schema and wrapper must both reject every mismatch. Positional constants or an equivalent exact schema binding must require the planned order. No reordering, relabeling, dropping, or acceptance by row count is allowed.

### BR-02 — Exact sealed design assignments and position

Independently mutate `design_entries`: duplicate, omit, foreign-slot substitute, and reorder without modifying cases. Use a wrong but schema-enumerated category, wrong ANCHOR/INVARIANT/MUTATION role, or wrong frozen anchor seed kind. The successor must enforce the planned slot order and frozen structural assignment at the partition boundary. It must not copy labels from cases to repair the draft. Variant seed kinds must not be newly prescribed where the inherited inventory leaves them open.

### BR-03 — Exact relation identity, order, and recipe

Use `relation_1` or an arbitrary opaque identifier instead of the required variant slot; duplicate or exchange two relations; change a valid family to a different allowed family; flip INVARIANT/SENSITIVE. All must fail at the affected partition. Mechanical endpoint assignment must derive from the frozen anchor and variant recipe, with distinct frozen case IDs. No relation row may migrate to another partition or be silently relabeled. Correct endpoint hashes cannot excuse the wrong family or mode.

### BR-04 — Complete immutable plan

Reject missing/repeated partition IDs, reordered partitions, duplicated or unassigned slots, moved variants, an anchor separated from its linked variants, a changed corpus order, and an extra or missing identity slot. Prove a bijection from the exact inherited inventory to all partition case/design slots and from the 16 recipes to relation slots. The plan remains 28/44/16. A valid positive run produces cases in the frozen 44-slot corpus order, with complete one-to-one sealed design and relation assignments. No adaptive repartition or slot-count arithmetic can manufacture coverage.

### BR-05 — Unique opaque IDs and frozen positional identity

Introduce collisions across two case IDs, across witness/source IDs in different slots, between a reserved distractor ID and a case/source ID, and in unused reserved positions. Introduce a malformed or category-bearing ID. Reject before discovery or generation. Require the complete frozen identity pool to have 528 unique UUIDv4 identities and exact slot coverage, then check actual output IDs match the frozen slot/position assignment. IDs cannot be regenerated during materialization or replaced to accommodate a malformed response.

### BR-06 — Freeze, request, schema, and configuration authority

Change the plan, a literal allowlisted artifact, code/schema source, a request spec, or configuration after freezing. Supply an otherwise valid unfrozen spec/config path; omit a required code/input entry from the freeze; replace a slot-bound schema with the historical permissive schema; add unauthorized request/config fields; use an external schema reference. The production entry point must reject before every network action. Reconstruct each sent request and prompt from the exact frozen spec and explicit configuration, including the actual output schema. A same-run canary must exercise the compact `$defs`/`prefixItems`/`const` schema support before authoring. A generic token response alone must not be claimed as proof that positional constraints worked. The trusted freeze and expected source authority must be explicit; mutable files cannot authenticate themselves merely by updating their own hashes.

### BR-07 — Invalid response preservation and strict JSON

Return malformed response text, duplicate JSON keys, NaN/Infinity, a complete JSON object with the wrong assigned slot, an incomplete/truncated envelope, forbidden tool fields, and an incomplete-read body. Verify exact returned raw bytes and available exact response text are retained, with receipt hashes computed over those bytes. Strict parsing rejects ambiguous JSON without repair. Preserve a parseable but invalid draft as a diagnostic artifact if that is the recorded policy; never materialize it as accepted. A transport interruption that returned no bytes must remain absent/null in custody, not a fabricated empty response.

### BR-08 — Mechanical transformation only

Use distinctive Unicode, whitespace, punctuation, projection text, hypotheses, guard declarations, map order, and selected anchors. After materialization, strip only the permitted mechanical fields and prove the remaining content is identical to the draft. Hash UTF-8 bytes, but count source-span and anchor offsets in Unicode code points as required by the frozen contract. Missing, empty, or repeated selected anchor text must fail; the wrapper must not choose the first match, normalize spelling, truncate a long claim, infer a map, or revise a hypothesis. A semantically dubious but structurally allowed hypothesis remains an unadjudicated hypothesis rather than being edited or certified by the wrapper.

### BR-09 — Terminal failure forbids the next network action

With a recording fake transport, fail a partition after generation by wrong slot, nonunique anchor, inherited structural word limit, and ordinary provider failure. Assert exactly the preceding successful calls and this failed call occur: no discovery, generate, retry, or later-partition request follows. A durable terminal/started marker blocks rerunning the same sequence, selecting a new attempt path inside it, or skipping directly to a later partition. Check failure at both the first partition and a later partition. Request-path success must not advance the sequence when partition materialization has failed.

### BR-10 — Fresh output paths preserve predecessors

Run against an existing empty directory, existing nonempty directory, existing call directory, a historical output path, and symlink/path aliases into frozen inputs. The entry point must fail before network I/O and preserve all prior bytes. An interrupted run cannot reuse its directory. A successor must have a separately identified output root; raw output, materialized files, final corpus, and receipts use exclusive writes. Path normalization and a frozen plan prevent a group ID or directory traversal from escaping the new run root. Diff/hash snapshots of the frozen framework and failed evidence must remain unchanged.

### BR-11 — The inherited full corpus gate remains authoritative

Use a complete 28-call structural positive fixture, then remove required declared guard coverage, violate a case/body/distractor word bound, alter full-fragment spans/hashes, or violate an inherited design/relation constraint that transport shape alone permits. Ensure the unchanged inherited validator is actually reached and controls the corpus result. Validate all 44 cases plus design and all 16 relations before publishing any corpus-ready status. A positive structural result must hash the exact final artifacts and say only what was checked. A/B/C, accepted expectations, semantic qualification, and assessor implementation stay NOT_RUN; Wave B stays LOCKED.

### BR-12 — Raw-to-corpus reconstruction prevents hand-edited materialization

Starting with recorded fake-transport success, change a parsed claim and its nearby digest while keeping the raw envelope; independently change a materialized claim and all internally consistent text hashes; supply complete hand-built `author-materialized` files and nominal PASS receipts with no raw calls; remove one raw response; swap a partition from another frozen ID plan. The audit/assembly gate must reject or deterministically reconstruct from the authoritative raw chain and refuse the altered artifacts. It must rebuild exact requests, strictly reparse raw responses, verify raw/text/parsed equality, repeat materialization, and compare final corpus hashes. Standalone frozen `assemble()` success must never be used as accepted-corpus provenance. Fully coordinated rewriting of every artifact and its trusted external authority cannot be detected by local hashes alone; the review will state that limit rather than claiming cryptographic provider attestation.

## Review method once the successor is ready

Record the exact successor commit and tree. Inspect only that commit's added code, tests, workflow, and local handoff, alongside the unchanged inherited source identities. Use a separate detached scratch checkout or exact-object source extraction; never edit the author agent's worktree. Run the author's focused suite in `<scratch>/biotech-test-env/bin/python`, then execute independent probes against the production entry point using fake transports only. Preserve commands, environment/version identity, exit status, and exact findings. Separate inherited repository lint debt from this wrapper's required lint/test gates.

Also inspect `plans/biotech-github-local-handoff-20261004.md` at the successor commit for executable local commands, explicit runtime configuration, bounded context/output budgets, schema-canary instructions, fresh output paths, and clear stop conditions. Corpus freeze is the authorized local stop; A/B remains NOT_RUN. The independent EB thread and its worktree/resources must remain separate. If a gap requires a revision, report a minimal reproduction and review a newly pinned commit rather than silently editing the candidate.
