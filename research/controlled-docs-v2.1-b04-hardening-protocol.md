# controlled-docs-v2.1 B04 hardening protocol

Status: preregistered successor design after the terminal v2 Slice 2 result.

## Why v2.1 exists

The first Slice 2 run on frozen `controlled-docs-v2` terminated
`BLOCK_SLICE3_BENCHMARK_NOT_DISCRIMINATING`.

Primary receipt:
- PR #6
- candidate `df300742db449effa6f47cc340e19bead015472a`
- workflow run `36514548709`
- artifact `11010463402`
- artifact digest `sha256:67507e3493d0e3fc9b3693acdc77a750bb22a907c2bd6f99fd4a086ee66ec6a8`

Every preregistered discriminator passed except B04: the naive MiniLM dense control recovered the
decisive numeric span inside top 3 on 11/11 committed B04 cases. The frozen v2 object is therefore
retained unchanged.

This v2.1 successor is an adaptive benchmark repair. It must not be described as independent
evidence that the original B04 design was hard.

## Objective

Strengthen the numeric-threshold surface so success requires discriminating the target numeric
fact from plausible approved/effective numeric alternatives, rather than merely locating the
correct topic or document.

The B03 and B04 discrimination floors remain unchanged from the failed v2 run. The repair changes
the benchmark, not the acceptance threshold.

## Protected objects

- `benchmarks/controlled-docs-v2/**` is read-only.
- v2.1 starts as a blob-identical copy of v2 under
  `benchmarks/controlled-docs-v2.1/**`.
- Corpus document and metadata bytes remain unchanged for this repair unless a separately recorded
  defect proves that existing sources cannot support the required cases.
- Existing v2 cases and gold remain historically recoverable.
- PR #6's first-run artifact remains the authority for the failure that motivated this successor.

## B04 numeric-collision rule

A new B04 repair case is admissible only when:

1. the answer is an explicit numeric value, range, duration, frequency, count, concentration,
   temperature, tolerance or limit in an Approved/Effective document;
2. the question does not contain the answer value;
3. the target is distinguishable from at least **three** Approved/Effective numeric alternatives
   that a superficially topical retriever could confuse with it;
4. at least one alternative is in the same governing document or same narrow process concept where
   practical;
5. the alternatives differ materially in value, unit, condition, grade, material, instrument,
   alert/action role or other authority-bearing qualifier;
6. each alternative is annotated as a `hard_negative` gold span;
7. the question identifies the intended condition strongly enough that a correct retriever can
   succeed without seeing evaluator-only labels;
8. the case is not created by inserting wording copied from the dense model's observed top hits.

The repair set should span several process areas and several collision types, rather than repeating
one table pattern.

## Information aperture for case authoring

The author may read:

- the frozen v2 runtime corpus;
- the B04 numeric-collision rule above;
- ordinary benchmark format/schema examples.

The author must not receive:

- MiniLM scores;
- MiniLM ranks;
- the identities of which v2 B04 chunks ranked above or below the target;
- the exact failed B04 per-case output from PR #6;
- instructions to make a named model fail.

The goal is to instantiate the failure mode, not adversarially target one model.

Because this supervisor context has already seen the failed dense rankings, it may prepare the
protocol and apparatus but should not be treated as a clean author of the new cases.

## Splits and independence

New committed repair cases may be used to qualify the evaluator but are marked as post-failure
repair cases. They do not restore independence to the reused v2 TEST set.

Before any Slice 3 promotion claim:
- the repaired discriminator must pass on committed v2.1 data; and
- the numeric-collision behavior must be reproduced on a fresh sealed/prospective set authored
  without exposure to candidate retrieval results.

If the existing sealed PROSPECTIVE set does not meet the v2.1 B04 rule, create a new v2.1
PROSPECTIVE identity rather than editing or relabelling the old commitment.

## Acceptance

The v2.1 Slice 2 rerun keeps the v2 preregistered floors:

- token-overlap B02 decisive-span recall@3 < 0.75;
- token-overlap B10 false-answer rate > 0.00;
- naive-dense B03 decisive-span recall@3 < 1.00;
- naive-dense B04 decisive-span recall@3 < 1.00;
- all other gaming and metamorphic controls as in PR #6.

The first complete v2.1 run is preserved whether it passes or blocks. Do not add or rewrite cases
after seeing that run and count a repaired rerun as the same candidate.

## Non-claims

A v2.1 pass would show that the benchmark rejects the named weak controls under this design. It
would not establish production retrieval quality, general numeric reasoning, or superiority of a
future candidate retrieval arm.
