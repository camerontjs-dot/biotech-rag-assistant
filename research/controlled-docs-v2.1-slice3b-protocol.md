# controlled-docs-v2.1 Slice 3B — DEV reranking and cross-reference protocol

Status: preregistered DEV-only challenger experiment. TEST and PROSPECTIVE remain untouched.

## Objective

Test the two remaining retrieval ideas that could plausibly earn a TEST slot:

1. bounded authored cross-reference admission for multi-passage cases;
2. bounded cross-encoder reranking over fixed first-stage candidate windows.

This stage does not change the frozen benchmark and cannot promote a production method.

## Fixed first-stage inputs

Reuse the exact Slice 3A definitions:

- `bm25_current`
- `rrf_bm25_bge`

The RRF arm uses the same structured index representation, BGE query instruction, model revision,
and k0=60 as Slice 3A.

No 3A score or parameter is retuned in 3B.

## Cross-reference challenger

`rrf_xref3`:

- start from the first two `rrf_bm25_bge` nominations;
- read only authored `relationships.json` edges with `kind == "retrievable"`;
- depth = 1;
- source documents are only the two nominated documents;
- among eligible referenced target documents, admit the chunk with the best original RRF rank;
- suppress duplicate chunk identities;
- add at most one cross-reference chunk;
- total evidence budget remains 3;
- if no eligible referenced chunk exists, use the original RRF rank-3 chunk.

No evaluator-only family/gold data is used to choose a reference target.

Hypothesis: authored links may improve B08 joint evidence without creating a general recall gain.

DEV selection rule: advance cross-reference admission only if B08 all-decisive case hit@3 improves over
plain RRF, aggregate decisive-span recall@3 falls by no more than 0.025 absolute, and B03/B04 do not
fall.

## Reranker candidate windows

Rerank the top 30 from each first-stage arm:

- `bm25_current`
- `rrf_bm25_bge`

Reranker text is the existing current representation
(`section_heading + verbatim chunk text`). First-stage ranks remain available in the JSON report.

Ties break by first-stage rank, then chunk identity.

## Reranker models

Small:

- `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision `588b01a83959436e6051d2133d8e9ecdcb28b1a5`

Larger:

- `cross-encoder/ms-marco-MiniLM-L12-v2`
- revision `e34b9c1a998b19a9937ee29985988737b2d4f7f8`

The chosen revisions are immutable weight-bearing revisions and are fixed before this DEV run.

Run four reranker arms:

- L6 over BM25 top-30;
- L12 over BM25 top-30;
- L6 over RRF top-30;
- L12 over RRF top-30.

For each first-stage window also run a deterministic seeded random permutation of the same 30
candidates as a gaming/ordering control.

## Reranker hypotheses

Potential help:
- B12 hard lexical distractors;
- B05 table-cell ordering;
- B02 paraphrase ordering at small K.

Potential harm that must be preserved:
- B06 conditions/exceptions;
- B07 negation/polarity.

A reranker is eligible for the TEST protocol only if on DEV:

1. aggregate decisive-span recall@3 is at least its own unreranked first-stage arm;
2. it improves B02, B05, or B12 case hit@3;
3. B06 and B07 case hit@3 do not fall;
4. B03 and B04 are not both reduced;
5. the seeded-random control does not meet or beat the reranker on aggregate recall@3;
6. stale leakage remains zero.

The L12 model advances only if it adds at least one decisive case at K=3 or improves aggregate MRR
by at least 0.02 over L6 on the same window without violating the family guards. Otherwise prefer
L6.

## Metrics

Same ranking metrics as Slice 3A at K=1/3/5, with per-family tables.

Also record:
- first-stage rank and reranked rank for each top-30 candidate;
- total reranking wall time;
- peak process RSS as an operational diagnostic;
- random-control result;
- B08 result for cross-reference admission.

## Answerability hypothesis

The cross-encoder answerability-score hypothesis from the parent Slice 3 plan remains advisory and
is not used to select a retrieval arm in 3B. Its withhold-decisive apparatus will be separately
preregistered before any score is interpreted as an answerability signal.

## After 3B

Freeze the TEST arm set and decision rule before any TEST case is read by a candidate arm.

PROSPECTIVE remains sealed.
