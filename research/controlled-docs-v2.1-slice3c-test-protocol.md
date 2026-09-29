# controlled-docs-v2.1 Slice 3C — preregistered TEST retrieval decision protocol

Status: preregistered before any Slice 3 candidate arm reads TEST.

## Objective

Run the smallest justified TEST comparison selected by DEV evidence and decide whether any retrieval
arm merits sealed PROSPECTIVE replication.

This stage may identify a provisional retrieval candidate. It cannot by itself promote product
behavior because PROSPECTIVE remains sealed and unevaluated.

## Frozen authority

Benchmark:
- tree SHA-256:
  `05f09c128a4848b57e607068fe59ff48f01e16387f2136083d289f331181ab85`
- freeze receipt SHA-256:
  `5c5cedbd872ca143cb581dc0e3686a45f6ab737ac0c74ef491f0c7849c817bbb`
- sealed PROSPECTIVE commitment:
  `07c7fb385d0792e1fa646ca47bb34aff3854142cb406bc57fc9514ab83f34ef0`

Predecessor evidence:
- Slice 2: `PASS_FOR_SLICE3_RETRIEVAL_COMPARISON`
- Slice 3A DEV artifact:
  `sha256:2b132170b59ef78205015550de92f706c01c27e2a44eb0cee20c3176b5fad175`
- Slice 3B DEV artifact:
  `sha256:36545aae56ee6db1bd97e0ecc49d0d7762ec0d60897ab3ec4eedf19976a3f6be`

TEST and sealed PROSPECTIVE were not used to select these arms.

## TEST arm set

Run exactly:

1. `bm25_current` — baseline/control
2. `minilm_current` — simple semantic challenger
3. `rrf_bm25_bge` — complementary first-stage fused challenger
4. `rerank_l6_bm25` — reranking challenger

All definitions are frozen from 3A/3B:

MiniLM:
- `sentence-transformers/all-MiniLM-L6-v2`
- revision `f5610b47471b118dafc55f4c387822dbfc8413ae`

BGE:
- `BAAI/bge-small-en-v1.5`
- revision `5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
- query prefix:
  `Represent this sentence for searching relevant passages: `

RRF:
- structured BM25 + structured BGE
- k0 = 60

Reranker:
- `cross-encoder/ms-marco-MiniLM-L6-v2`
- revision `588b01a83959436e6051d2133d8e9ecdcb28b1a5`
- rerank BM25-current top 30
- current representation for cross-encoder text
- ties: first-stage rank, then chunk identity

Pin `sentence-transformers==6.1.0`.

No L12 reranker, fixed score fusion, structured MiniLM, standalone BGE, authored-link expansion,
query rewriting, answerability threshold, generator, or other challenger enters TEST.

## Primary metric

Primary TEST metric:

**mean per-case decisive-span recall@3 over answerable TEST cases.**

Each answerable case has equal weight; a multi-passage case contributes its fraction of decisive
spans recovered inside the top-3 evidence budget.

The minimum effect worth acting on is:

**+0.050 absolute recall@3 over `bm25_current`.**

This threshold was chosen from DEV before TEST: the selected first-stage challengers improved by
about 0.05–0.07 on DEV, while the selected reranker improved by about 0.10. A smaller TEST effect is
treated as too small to justify added retrieval machinery.

## Paired statistics

For each challenger versus BM25:

1. compute the paired per-case recall@3 difference;
2. run 10,000 paired bootstrap resamples over answerable case IDs with seed `20260929`;
3. report the percentile 95% interval for the mean recall@3 difference;
4. require the lower bound to be greater than 0 for eligibility.

Also report exact two-sided McNemar on all-decisive case hit@3:
- `b`: BM25 miss / challenger hit
- `c`: BM25 hit / challenger miss
- exact two-sided binomial p-value

McNemar is corroborating evidence, not a separate promotion gate.

## Non-compensable and family guards

Every eligible challenger must have:
- stale/draft/obsolete leak count = 0;
- all-decisive case hit@3 no lower than BM25;
- B01 case hit@3 = 1.00;
- B03 case hit@3 >= 0.80;
- B04 case hit@3 >= 0.90;
- B06 case hit@3 >= BM25 B06;
- B07 case hit@3 >= BM25 B07;
- B08 all-decisive case hit@3 >= BM25 B08.

These reliability guards do not compensate against the primary metric.

## Eligibility

A challenger is eligible for PROSPECTIVE replication only if all are true:

1. primary recall@3 delta versus BM25 >= +0.050;
2. paired bootstrap 95% interval lower bound > 0;
3. all-decisive case hit@3 does not fall;
4. every family guard above passes;
5. stale leakage remains zero.

No TEST threshold, arm definition, family floor, or model identity may change after the first TEST
measurement and still count as this candidate.

## Multiple eligible challengers

If exactly one challenger is eligible, it becomes the provisional candidate.

If multiple challengers are eligible:
1. identify the highest primary recall@3;
2. any challenger within 0.025 absolute of that best result enters a pairwise bootstrap comparison
   with the best;
3. if that pairwise 95% interval includes zero, treat the difference as inconclusive and prefer the
   simpler architecture.

Predeclared simplicity order:

`minilm_current` < `rrf_bm25_bge` < `rerank_l6_bm25`

This order reflects one neural retrieval stage, then two first-stage retrieval signals, then a
sequential retrieval-plus-cross-encoder stage.

If a challenger exceeds the best simpler arm by more than 0.025 and the pairwise interval excludes
zero in its favour, prefer the stronger arm.

## No eligible challenger

If no challenger is eligible, retain BM25 as the retrieval baseline and record Slice 3 as negative.
Do not mine secondary metrics to select a winner.

## Diagnostics

Report, but do not mine for promotion:
- recall@1 and @5;
- MRR;
- per-family tables;
- B02, B05, B12, B13;
- B10/B11 retrieval observations;
- semantic-model truncation;
- reranker wall time and peak process RSS.

## After TEST

TEST chooses at most one provisional candidate for sealed PROSPECTIVE replication.

Before the sealed object is read:
- commit a separate PROSPECTIVE replication protocol;
- preserve the exact candidate configuration;
- define the replication gate against BM25;
- then run the sealed set locally.

A reranking candidate must repeat its gain on PROSPECTIVE before promotion, as required by the
parent Slice 3 plan.

No public/product retrieval behavior is promoted by this TEST stage alone.
