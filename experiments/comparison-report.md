# Semantic vs BM25 retrieval — comparison report

Gated experiment (ADR-009 / ADR-012): does semantic or hybrid retrieval beat the deterministic BM25 baseline on the synthetic controlled-document corpus, while preserving the off-topic refusal behavior? Same status-gated chunks for every method.

- Corpus chunks: 18 (Approved/Effective only)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (bi-encoder, CPU, cached locally)
- Methods: `bm25` (production baseline), `semantic` (MiniLM cosine), `hybrid` (RRF k0=60 of bm25+semantic)

## Retrieval quality

Recall@k = fraction of on-topic queries whose relevant document appears in the top k chunks. MRR = mean reciprocal rank of the first relevant-document chunk.

### All on-topic queries (n=16)

| method | recall@1 | recall@3 | recall@5 | MRR |
|---|---:|---:|---:|---:|
| bm25 | 0.69 | 0.69 | 0.81 | 0.74 |
| semantic | 1.00 | 1.00 | 1.00 | 1.00 |
| hybrid | 0.88 | 1.00 | 1.00 | 0.92 |

### Easy on-topic queries (n=8)

| method | recall@1 | recall@3 | recall@5 | MRR |
|---|---:|---:|---:|---:|
| bm25 | 1.00 | 1.00 | 1.00 | 1.00 |
| semantic | 1.00 | 1.00 | 1.00 | 1.00 |
| hybrid | 1.00 | 1.00 | 1.00 | 1.00 |

### Hard on-topic queries (n=8)

| method | recall@1 | recall@3 | recall@5 | MRR |
|---|---:|---:|---:|---:|
| bm25 | 0.38 | 0.38 | 0.62 | 0.49 |
| semantic | 1.00 | 1.00 | 1.00 | 1.00 |
| hybrid | 0.75 | 1.00 | 1.00 | 0.83 |

## Off-topic refusal / separation

Can a single top-1-score threshold reject all off-topic queries without rejecting any on-topic query? (A clean gap means a reliable refusal gate is achievable.)

| method | min on-topic top | max off-topic top | clean threshold? |
|---|---:|---:|:--:|
| bm25 | 2.115 | 3.119 | NO |
| semantic | 0.350 | 0.244 | yes |
| hybrid | 0.032 | 0.033 | NO |

Production coverage gate (BM25 rank-1 coverage ≥ 0.6, ADR-012): refuses 6/6 off-topic; wrongly refuses 9/16 on-topic.

## Per-query first-relevant rank (hard paraphrases)

| query | bm25 | semantic | hybrid |
|---|---:|---:|---:|
| hard-em-excursion | 5 | 1 | 1 |
| hard-deviation-escalate | 1 | 1 | 1 |
| hard-outdated-procedure | 7 | 1 | 3 |
| hard-gowning-reprove | 7 | 1 | 3 |
| hard-scale-fails | 1 | 1 | 1 |
| hard-skip-water-check | 6 | 1 | 1 |
| hard-area-clear | 1 | 1 | 1 |
| hard-client-demands | 4 | 1 | 1 |
## Verdict and recommendation

- **Best on hard paraphrases:** `semantic` (hard MRR: bm25 0.49, semantic 1.00, hybrid 0.83). Easy queries tie — the whole gain is on paraphrases the lexical baseline misses.
- **Refusal is cleaner with semantic:** one cosine threshold (~0.30) separates all on-topic from all off-topic (0.244 < 0.350); raw BM25 score cannot (why ADR-012 gates on coverage, not score). The current gate wrongly refuses 9/16 on-topic queries — mostly the hard paraphrases.
- **Hybrid (RRF) is not the answer here:** it dilutes semantic's top-1 ranking and its fused scores don't support a clean refusal threshold.

**Recommendation:** promote **semantic retrieval with a cosine refusal threshold** next — not hybrid — replacing the coverage gate's refusal-bias while keeping every deterministic trust control (status gating, citation validation, audit, current-version invariant) unchanged around it. Validate the threshold on a larger, ideally real corpus first: the gap here is real but narrow and the paraphrases were hand-written.

## Limits

Synthetic 10-document corpus; small labeled set. Results are directional, not a production validation. The refusal threshold for semantic/hybrid is analyzed here, not yet implemented. Promotion into the package remains gated on this evidence plus keeping stale-document exclusion, refusal, and citation checks green.
