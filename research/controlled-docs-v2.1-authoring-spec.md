# controlled-docs-v2.1 numeric-collision authoring specification

## Objective

Add eight new B04 numeric-threshold cases to the construction benchmark so the numeric surface
requires choosing the governing numeric fact among several plausible Approved/Effective numeric
alternatives.

This document defines case quality only. Do not run or target any retrieval model while authoring.

## Case count and split

Create exactly eight new cases:
- four DEV;
- four TEST.

Use process areas already assigned to the corresponding split. Cover at least three distinct process
areas in DEV and at least three distinct process areas in TEST.

Use IDs:
- `C-DEV-0121` through `C-DEV-0124`;
- `C-TEST-0125` through `C-TEST-0128`.

## Numeric-collision rule

Every new case must satisfy all of the following:

1. Primary family is `B04` (`numeric threshold`).
2. Expected disposition is `answer`.
3. Exactly one decisive Approved/Effective span contains the requested numeric fact.
4. The question does not contain the answer value.
5. At least three Approved/Effective `hard_negative` spans contain plausible competing numeric
   facts.
6. At least one hard negative is in the same governing document as the decisive span.
7. Competing spans differ materially in value, unit, condition, grade, material, instrument,
   alert/action role, duration type, sample type or another authority-bearing qualifier.
8. The question contains enough condition/context to make one span correct without evaluator-only
   labels.
9. The eight cases must use several collision shapes. Do not repeat one table pattern.
10. Corpus document and metadata bytes do not change.

Useful collision shapes include, without requiring these exact choices:
- alert versus action level;
- one grade versus another grade;
- PW versus WFI;
- dirty versus clean hold;
- one alarm or review interval versus another;
- one material/sample type versus another;
- one chamber/condition versus another;
- one tolerance or calibration stage versus another.

## Gold

For each new case:
- annotate the decisive span with `decisive: true`, `relevance_class: decisive_support`, the
  required fact/value and exact Python-character offsets;
- annotate at least three competing Approved/Effective spans with
  `decisive: false`, `relevance_class: hard_negative`;
- all spans must round-trip exactly against source bytes;
- use the existing gold schema unchanged.

## Family metadata

Each new family entry must contain both tags:
- `numeric_collision`
- `post_failure_repair`

Do not encode model names, scores, expected model behavior or retrieval results in the cases,
family data, gold or rationales.

## Files allowed to change

Only:
- `benchmarks/controlled-docs-v2.1/cases/dev_cases.jsonl`
- `benchmarks/controlled-docs-v2.1/cases/test_cases.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/gold/dev_relevance.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/gold/test_relevance.jsonl`
- `benchmarks/controlled-docs-v2.1/evaluator_only/families.json`
- `benchmarks/controlled-docs-v2.1/evaluator_only/lexical_overlap.json`
- `benchmarks/controlled-docs-v2.1/corpus_manifest.json` for case counts and authoring provenance.

Do not add `SHA256SUMS` or `freeze_receipt.json`.

## Acceptance

Run the committed acceptance script:

```bash
python research/controlled_docs_v21_acceptance.py \
  --v2 benchmarks/controlled-docs-v2 \
  --v21 benchmarks/controlled-docs-v2.1
```

It must pass before handoff.

Do not run semantic retrieval, BM25 comparison experiments, reranking, or any benchmark
discriminator while authoring.
