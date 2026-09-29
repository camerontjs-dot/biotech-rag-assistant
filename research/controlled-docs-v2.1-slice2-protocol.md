# controlled-docs-v2.1 Slice 2 discriminator protocol

Status: preregistered rerun protocol for the first and only Slice 2 measurement against the frozen
`controlled-docs-v2.1` candidate.

## Objective

Determine whether the repaired v2.1 benchmark now rejects the same deliberately weak systems that
the frozen v2 benchmark failed to discriminate, without changing the evaluator, weak-control model,
or acceptance floors after observing v2.1 results.

A pass authorizes Slice 3 retrieval-arm comparison in a separate successor. It does not promote any
retrieval method.

## Frozen benchmark authority

- benchmark: `benchmarks/controlled-docs-v2.1`
- tree SHA-256:
  `05f09c128a4848b57e607068fe59ff48f01e16387f2136083d289f331181ab85`
- freeze receipt SHA-256:
  `5c5cedbd872ca143cb581dc0e3686a45f6ab737ac0c74ef491f0c7849c817bbb`
- v2.1 sealed prospective commitment:
  `07c7fb385d0792e1fa646ca47bb34aff3854142cb406bc57fc9514ab83f34ef0`
- historical v2 prospective commitment is preserved separately and is not used as v2.1 prospective
  evidence:
  `ab33beee9866e54a16060c595267c95dd7e0db1c48dc2c51ca3857a2d9100d07`

The sealed v2.1 PROSPECTIVE bytes remain outside Git and are not used in Slice 2.

## Predecessor result

The first Slice 2 run on frozen v2 terminated:

`BLOCK_SLICE3_BENCHMARK_NOT_DISCRIMINATING`

The only failed preregistered discriminator was B04: the naive dense control achieved 11/11
decisive-span recall@3. That result is preserved in closed PR #6.

v2.1 repairs the benchmark rather than weakening the B04 floor.

## Evaluator identity

The evaluator implementation is byte-for-byte copied from the PR #6 first-run evaluator and exposed
here as:

`research/controlled_docs_v21_slice2.py`

The weak dense control remains:

- model: `sentence-transformers/all-MiniLM-L6-v2`
- revision: `f5610b47471b118dafc55f4c387822dbfc8413ae`
- package: `sentence-transformers==6.1.0`

No candidate retrieval arm is implemented in this slice.

## Predeclared floors

Unchanged from the failed v2 run:

| Surface | Requirement |
| --- | ---: |
| B02 token-overlap decisive-span recall@3 | < 0.75 |
| B10 token-overlap false-answer rate | > 0.00 |
| B03 naive-dense decisive-span recall@3 | < 1.00 |
| B04 naive-dense decisive-span recall@3 | < 1.00 |

The oracle must reach ceiling. Null, first-N, return-everything, corrupted-provenance,
hard-negative-biased, answerability-liar and status-gate-removed controls must be rejected on their
intended surfaces.

Metamorphic requirements are unchanged:
- source-order permutation leaves judgments unchanged;
- duplicate insertion earns no extra credit;
- mutating a gold span changes the corresponding judgment;
- `withhold_decisive` removes decisive chunks.

## One-shot rule

Run this discriminator once on the frozen v2.1 identity.

If it returns `PASS_FOR_SLICE3_RETRIEVAL_COMPARISON`, preserve the complete report and continue to
Slice 3 in a separately identified successor.

If it returns `BLOCK_SLICE3_BENCHMARK_NOT_DISCRIMINATING`, preserve the complete result. Do not
change floors, cases, gold, or weak-control configuration and call a rerun the same candidate.

If the evaluator cannot complete because of an apparatus/infrastructure defect, preserve the failed
attempt and diagnose the apparatus separately before deciding whether a valid measurement was ever
entered.

## Evidence handling

The workflow must upload the JSON and Markdown reports before enforcing the evaluator exit code.
A scientific BLOCK therefore remains inspectable even when the job concludes red.

## Non-claims

- Slice 2 evaluates benchmark discrimination, not production retrieval quality.
- MiniLM is a deliberately weak control here, not a candidate.
- PROSPECTIVE remains sealed and unevaluated.
- A pass authorizes comparison work only.
