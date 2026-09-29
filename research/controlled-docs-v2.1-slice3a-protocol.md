# controlled-docs-v2.1 Slice 3A — DEV first-stage retrieval protocol

Status: preregistered DEV-only experiment. TEST and sealed PROSPECTIVE remain untouched.

## Objective

Measure whether richer index-time representation and small semantic retrieval improve decisive-span
nomination over the existing BM25 representation on DEV, before selecting any arm for TEST.

This stage is exploratory within the frozen benchmark but is still evidence-producing. It may select
which arms advance to the preregistered TEST comparison; it cannot promote retrieval behavior.

## Frozen authority

- benchmark tree SHA-256:
  `05f09c128a4848b57e607068fe59ff48f01e16387f2136083d289f331181ab85`
- freeze receipt SHA-256:
  `5c5cedbd872ca143cb581dc0e3686a45f6ab737ac0c74ef491f0c7849c817bbb`
- Slice 2 disposition:
  `PASS_FOR_SLICE3_RETRIEVAL_COMPARISON`
- Slice 2 workflow:
  `36593613691`
- Slice 2 artifact:
  `11044099713`
- sealed PROSPECTIVE commitment:
  `07c7fb385d0792e1fa646ca47bb34aff3854142cb406bc57fc9514ab83f34ef0`

DEV contains 44 cases. This stage must not read TEST cases/gold or the sealed PROSPECTIVE bytes.

## Representation arms

Stored evidence remains the existing verbatim `DocumentChunk.text` plus exact offsets. Representation
changes affect index text only.

### current

Existing production representation:

`section_heading + "\n" + verbatim chunk text`

### structured

Index text adds:

1. document title;
2. hierarchical Markdown section path at the chunk's source position;
3. the same verbatim chunk text.

If a table header is already inside the verbatim chunk, do not duplicate it. No generated summary or
LLM-authored metadata is added.

Representation code must demonstrate that source offsets and stored quote bytes are unchanged.

## First-stage arms

Run these on DEV:

1. `bm25_current`
2. `bm25_structured`
3. `minilm_current`
4. `minilm_structured`
5. `bge_structured`
6. `rrf_bm25_bge` — reciprocal-rank fusion, k0=60
7. `fusion50_bm25_bge` — fixed 0.50/0.50 per-query min-max score fusion

No reranker, cross-reference expansion, query rewriting, generator, or answerability classifier is in
3A. Those are later challengers only if first-stage evidence justifies them.

## Model identities

MiniLM weak/reference semantic arm:

- `sentence-transformers/all-MiniLM-L6-v2`
- revision `f5610b47471b118dafc55f4c387822dbfc8413ae`

Second small semantic arm, chosen before this DEV run:

- `BAAI/bge-small-en-v1.5`
- revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`

For BGE retrieval queries use the model's retrieval instruction:
`Represent this sentence for searching relevant passages: `

Pin `sentence-transformers==6.1.0`.

## Metrics

For answerable DEV cases:

- decisive-span recall@1, @3, @5;
- all-decisive case hit@1, @3, @5;
- MRR of the first decisive span;
- per-family results;
- B08 joint-group all-evidence hit;
- B06/B07 qualifier and negation diagnostics;
- B04 numeric-collision diagnostics.

For all arms:

- stale/draft/obsolete leak count, non-compensable and required to stay zero;
- duplicate source-span burden;
- number of indexed texts exceeding each semantic model's declared max sequence length before
  truncation.

B10 and B11 are reported as diagnostics only in 3A. No refusal threshold is tuned here.

## DEV interpretation

3A does not have a promotion threshold because TEST has not been entered. Use DEV to narrow the arm
set and to preregister the TEST decision rule.

Prefer simpler arms when DEV differences are negligible.

Representation is retained for TEST only if it improves or holds aggregate recall@3 without reducing
B03, B04, B06, or B07 case hit@3.

A semantic or fused arm is eligible for the TEST protocol only if, on DEV:

- stale leak remains zero;
- decisive-span recall@3 is no worse than `bm25_current`;
- it improves at least one of B02, B08, B12, or B13 without reducing both B03 and B04;
- observed truncation is recorded rather than silently ignored.

These are arm-selection rules, not final promotion rules.

## After DEV

After the first DEV artifact is preserved:

1. choose the smallest justified set of arms for TEST;
2. preregister a primary TEST metric, minimum effect, family floors, paired statistics and tie rule;
3. preregister reranker hypotheses before any reranker sees TEST;
4. only then enter TEST.

Do not inspect or use sealed PROSPECTIVE until the later protocol explicitly requires disjoint
replication.

## Evidence handling

Write JSON and Markdown reports and upload them before enforcing any experiment exit status. Preserve
negative and inconvenient results.
