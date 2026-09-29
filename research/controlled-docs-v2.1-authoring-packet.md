# CONTEXT-FREE REQUIRED — controlled-docs-v2.1 B04 case authoring

## Objective

Author exactly eight new committed `numeric_collision` cases for the controlled-docs-v2.1
benchmark: four DEV and four TEST. The cases must exercise numeric-threshold retrieval where the
target numeric fact competes with several plausible Approved/Effective numeric alternatives.

This task authors benchmark data only. Do not run retrieval models and do not attempt to make any
named model fail.

## Frozen authority

Repository: `camerontjs-dot/biotech-rag-assistant`

Allowed benchmark source:
- PR #4 / commit `379a3e65942e8af7dcf21a4d24077642d45b364d`
- `benchmarks/controlled-docs-v2/corpus/**`
- existing runtime/evaluator schemas under `benchmarks/controlled-docs-v2/{cases,evaluator_only}/`
  only as format examples
- `research/controlled-docs-v2.1-b04-hardening-protocol.md`
- `research/controlled_docs_v21_acceptance.py`

The corpus document and metadata bytes are fixed. Use existing Approved/Effective source text only.

## Forbidden pre-freeze information

Do not read:
- PR #6 discussion, comments or artifacts;
- `research/controlled_docs_v2_slice2.py` results or reports;
- workflow run `36514548709`;
- any MiniLM, BM25 or other retrieval rankings/scores for B04;
- prior analysis of which B04 cases were easy or hard;
- candidate retrieval code beyond what is required to understand case file schemas.

If forbidden information is exposed, report contamination and stop. Do not try to restore
independence by opening another branch in the same informed context.

## Authoring rule

Each new case must satisfy the B04 numeric-collision rule in
`research/controlled-docs-v2.1-b04-hardening-protocol.md`.

In particular:
- answer is an explicit numeric fact from an Approved/Effective document;
- question does not contain the answer value;
- at least three Approved/Effective numeric hard-negative spans are plausible alternatives;
- at least one hard negative is in the same governing document;
- hard negatives differ materially by value, unit, condition, grade, material, instrument,
  alert/action role or another authority-bearing qualifier;
- cases span several process areas and collision types;
- do not repeat one table pattern eight times.

Use four DEV process areas already assigned to DEV and four TEST cases from TEST-assigned process
areas. Do not move a process area across splits.

## Output

Work on branch `research/controlled-docs-v2.1-b04-hardening`.

Add exactly eight cases:
- IDs `C-DEV-0121` through `C-DEV-0124`;
- IDs `C-TEST-0125` through `C-TEST-0128`.

Update only these v2.1 benchmark files:
- `benchmarks/controlled-docs-v2.1/cases/dev_cases.jsonl`
- `benchmarks/controlled-docs-v2.1/cases/test_cases.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/gold/dev_relevance.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/gold/test_relevance.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/families.json`
- `benchmarks/controlled-docs-v2.1/evaluator_only/lexical_overlap.json`
- `benchmarks/controlled-docs-v2.1/corpus_manifest.json` only for updated case counts and
  authoring provenance.

For every new family record add both tags:
- `numeric_collision`
- `post_failure_repair`

Do not create `SHA256SUMS` or `freeze_receipt.json`. Freezing occurs only after acceptance and
the new PROSPECTIVE identity are resolved.

## Verification

Run:

```bash
python research/controlled_docs_v21_acceptance.py \
  --v2 benchmarks/controlled-docs-v2 \
  --v21 benchmarks/controlled-docs-v2.1
```

It must pass before handoff.

Also run normal repository tests relevant to corpus parsing. Do not run MiniLM, semantic retrieval,
BM25 comparison experiments or the Slice 2 evaluator in this context.

## Handoff

Return:
- final commit SHA;
- eight case IDs and process areas;
- acceptance-script output;
- files changed;
- explicit contamination status.

Stop after authoring/acceptance. Do not run the retrieval discriminator.
