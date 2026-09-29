# controlled-docs-v2 Slice 2 evaluator protocol

Status: preregistered research-infrastructure protocol for the first Slice 2 run.

## Objective

Determine whether the frozen `controlled-docs-v2` benchmark and diagnostic evaluator can
distinguish deliberately weak or gaming systems before any new retrieval method is compared for
promotion.

A pass authorizes Slice 3 comparison work only. It does not promote BM25, dense retrieval, hybrid
retrieval, reranking, or any production behavior.

## Frozen authority

- Parent benchmark PR: #4
- Frozen parent commit: `379a3e65942e8af7dcf21a4d24077642d45b364d`
- Benchmark tree receipt: `bbf8410cf9da9c82bc04b31a731241b197d9827b58f31842de5496a12b364670`
- PROSPECTIVE commitment:
  `ab33beee9866e54a16060c595267c95dd7e0db1c48dc2c51ca3857a2d9100d07`
- DEV/TEST benchmark bytes are read-only in this successor.
- PROSPECTIVE remains sealed and is not required for Slice 2.
- Dense control model:
  `sentence-transformers/all-MiniLM-L6-v2` at revision
  `f5610b47471b118dafc55f4c387822dbfc8413ae`.
- `sentence-transformers` package: `6.1.0`.

If the frozen benchmark itself needs correction, stop. Do not repair it in this branch.

## Runtime/evaluator aperture

The system-under-test side may read:

- `corpus/`
- `cases/dev_cases.jsonl`
- `cases/test_cases.jsonl`

The diagnostic evaluator separately reads `evaluator_only/` after retrieval output exists. Runtime
case files remain free of family labels, gold, rationales, and expected results.

## Span scoring

A retrieved chunk earns decisive-span credit only when all of these match a decisive gold row:

1. `doc_id`;
2. `version`;
3. a non-empty character-span intersection.

Duplicate copies of the same source span earn no additional credit.

`withhold_decisive` is implemented by removing every retrievable chunk that overlaps a decisive
gold span before retrieval. For an originally answerable case, the resulting answer disposition is
`not_stated`.

## Predeclared discrimination floors

These are benchmark-discrimination criteria, not production retrieval thresholds.

| Surface | Floor |
|---|---:|
| B02 paraphrase decisive-span recall@3 | 0.75 |
| B03 identifier decisive-span recall@3 | 1.00 |
| B04 numeric-threshold decisive-span recall@3 | 1.00 |
| B10 fact-not-stated false-answer rate | 0.00 maximum |

Rationale:

- B02 must require more than a simple lexical shortcut on a family deliberately authored for low
  overlap. Nine of twelve committed cases is the minimum acceptable floor.
- B03 opaque identifiers and B04 exact numeric thresholds are precision-sensitive surfaces. A weak
  dense-only control must not satisfy the same gate as a later candidate by dropping even one
  committed case at the generator's top-3 evidence budget.
- B10 contains no answer in the approved corpus. Any control that claims an answer fails the floor.

Do not weaken these values after the first measurement and still call the rerun the same experiment.

## Controls

The first run includes:

- null;
- gold oracle;
- first-N/source order;
- token-overlap lexical retriever;
- return-everything under the top-K budget;
- corrupted provenance;
- hard-negative-biased retrieval;
- answerability liar;
- naive dense-only retrieval;
- BM25 with the status gate removed;
- existing BM25 plus the ADR-012 coverage gate.

The dense-only system is a control, not a candidate retrieval implementation.

## Gate

Slice 2 passes only when all are true:

1. the oracle reaches ceiling;
2. token overlap fails both the B02 and B10 floors;
3. naive dense-only fails both the B03 and B04 floors;
4. every other gaming control is detected on its intended surface;
5. source-order permutation leaves the diagnostic judgment unchanged;
6. duplicate insertion earns no extra credit;
7. mutating a gold span changes the corresponding judgment;
8. the `withhold_decisive` aperture removes all decisive chunks.

A failure is terminal for this Slice 2 candidate. Preserve the result. If the failure is an
apparatus defect, fix it in a successor identity and state why the first result was invalid. If a
weak system legitimately passes a decisive benchmark floor, the benchmark is non-discriminating
for that surface and Slice 3 remains blocked until a new benchmark version is justified.

## Required outputs

The run writes:

- `slice2-results.json`, including per-case and per-family observations;
- `slice2-report.md`, including the gate and non-claims.

CI uploads both as the primary run artifact. The PR records the exact candidate SHA and workflow
identity.
