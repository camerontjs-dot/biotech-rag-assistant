# Author corpus freeze: APPARATUS_INVALID

The request-bound authoring milestone remains valid: every one of the 28 frozen
partitions produced one complete response that passes its transport JSON schema.
Mechanical corpus freezing exposed a separate failure. Those responses contain
44 case rows, but only **33 unique planned slots**. Eleven required variant or
mutation slots are absent. The unchanged frozen materializer rejects ten of the
28 partitions. No valid full `cases.jsonl`, `design.json`, or `relations.json` was
created, and no A/B/C adjudication was run.

This is terminal **APPARATUS_INVALID** for the current author-corpus candidate.
It is not a semantic disagreement result. The semantic question remains unresolved.

## Pinned inputs and authority

- Source: PR #51 head `bf07ea3b16854830a9a2ec5a0c9725488bb02f17`, tree
  `cdb440064c4ec469aa7bc48d8bfc7fd3e5185a91`.
- Frozen PR #30 design publication: `d1e092b7cdb878d064735d597e8c3b2d6c710157`.
- Frozen materializer: `research/build_semantic_author_requests.py`, SHA-256
  `aa70e5aecdbfadcc000694b72bce82f5b9410940167ca46a74671fb599dc1a4c`.
- Frozen structural validator: `research/check_semantic_assessor_preparation.py`,
  SHA-256 `9bbaa06b84f9632bb4d2305c0a9798a853466e286604aaa89036145562ebc718`.
- All artifact hashes in the three retained apparatus freezes were verified.

`case-construction.md` requires exactly 44 assigned packets and preserves incomplete
authoring as `NOT_READY`. `SCHEMAS.md` requires frozen corpus validation, including
slot and endpoint assignments. `adjudication.md` assigns malformed packets/output
to `APPARATUS_INVALID`; its `INCONCLUSIVE` category concerns semantic ambiguity,
agreement, expectations, and required semantic opportunities. The exact governing
paths, line references, and SHA-256 identities are in `TERMINAL.json`.

## What the unchanged materializer rejected

| Check | Failed partitions |
| --- | --- |
| Case slot/order | author-01, author-09, author-10, author-12, author-16, author-18 |
| Design slot assignment | author-11 |
| Relation slot assignment | author-02, author-15, author-21 |

For example, author-01's required slots were `anchor_01`, `invariant_1`, and
`mutation_1`, `mutation_3`, `mutation_4`, `mutation_5`, `mutation_6`. Its canonical
response returned `anchor_01` through `anchor_07`. No identifier was changed to
force it into the planned inventory. The full identifier-only comparison is in
`identifier-checks.json`; no author hypotheses or case prose are copied into it.
Checking all identifier dimensions without stopping at the first error also shows
that all 16 returned relation identifiers differ from their frozen required
identifiers across the ten partitions that contain relations. This is a structural
identity finding; it makes no claim about the semantic correctness of their text.

All missing slots are retained in `slot-proof.json`: `invariant_1`, `invariant_2`,
`invariant_4`, `invariant_5`, `invariant_8`, `mutation_1`, `mutation_3`, `mutation_4`,
`mutation_5`, `mutation_6`, and `mutation_7`.

The transport schema checks shape and row count. It does not establish exact slot
assignment. The frozen materializer's stronger checks behaved as intended and
prevented incomplete inputs from reaching adjudication. Eighteen partitions
materialized individually; this is diagnostic partial output, not a corpus freeze.

## Canonical attempts and preserved failures

`canonical-attempt-policy.json` and `canonical-attempt-map.json` record the first
complete schema-valid response in each frozen partition, ordered mechanically by
recorded call time. No semantic quality selection occurred. There is only one
complete response per partition.

Author-01 and author-12 select their recorded second attempts; author-20 selects
its second attempt after interruption. Their prospective corrections precede the
respective send timestamps in retained Git history (`correction-lineage.json`).
Author-03 selects its sole `author-03-budget` response. The original budget's lack
of semantic acceptance is retained; later schedules already name that recorded
response, and the current operator instruction authorizes mechanical freezing.

All **31 requests** reconstruct byte for byte from frozen specs and configurations.
All **30 returned raw response hashes** match receipts. All **28 complete response
texts and parsed outputs** reconstruct byte for byte and pass transport schemas.
The manifest hashes all **301 available attempt artifacts**, including two truncated
raw responses and the five author-20 attempt-1 files. The absent response is recorded
as absent, with a null hash, not as a fabricated empty response.

Retained requests and receipts identify the author runtime as Ollama `0.35.1`,
model `qwen3.5:9b`, digest
`6488c96fa5faab64bb65cbd30d4289e20e6130ef535a93ef9a49f42eda893ea7`.
Configurations, exact requests, and selected model identities are preserved.
Full local model inventories were intentionally unpublished in the original
lineage. Their reported hashes remain hash-only and are not independently verified
here. Provider-hidden context remains `UNKNOWN`.

## Reproduction and attempt history

Use Python with `jsonschema==4.25.1`, the checked-in reconstruction harness, a
clean detached checkout at the pinned source SHA, and a new output directory:

```sh
python reconstruct_corpus.py --source /path/to/pinned-checkout --output /path/to/new-reconstruction
```

The harness never invokes a provider, adjudicator, reducer, or project generator.
It invokes the unchanged frozen materializer in an isolated staging tree containing
exact copies of selected raw outputs and frozen inputs. A successfully completed
harness process can report `AUTHOR_CORPUS_NOT_READY`; process completion is not a
passing corpus gate.

The first reconstruction stopped on the failed slot proof. Its script snapshot,
execution receipt, environment identity, and slot proof remain preserved. The second
attempt added diagnostic replay of every partition without altering the acceptance
gate, source, attempt selection, or authored content. A separate diagnostic call to
the unchanged assembler rejected the missing author-01 materialization before any
full corpus output could be written (`assembly-attempt.json`, `assembly-error.log`).
The log replaces only the scratch root prefix; its raw counterpart is retained
locally. These are mechanical replays, not independent authoring replications. The root
review separately enumerated the raw slot fields without consuming the materializer
or this worker's slot proof; `root-slot-verification.json` reproduces the 44/33/11
counts. A fresh identifier-only reviewer also verified cases, design entries,
and relation IDs directly against frozen partitions and checked all 28 selected
raw/parsed responses (`independent-slot-crosscheck.json`). It found 37 unique
planned design slots, seven missing planned design slots, six duplicated design
identifiers, and one unexpected identifier. None of the 16 returned relation IDs
matches a required relation-slot identifier. Only its absolute scratch prefix is
projected out; source/projection hashes are retained. These are mechanical
checks, not independent semantic or human agreement.

## Terminal boundary

A/B/C, comparison, reconciliation, author-design reveal to adjudicators, semantic
assurance, and assessor implementation remain `NOT_RUN`. Wave B remains `LOCKED`.
No role or runtime identity is invented for an unexecuted adjudicator.

Do not relabel, repair, drop, or re-author cases inside this candidate. A prospective
successor may test an authoring mechanism that enforces the already frozen slot
assignments at the output boundary. Such a successor must preserve this failure and
establish fresh corpus validity before any semantic adjudication. This record does
not authorize a new call or supply semantic labels.
