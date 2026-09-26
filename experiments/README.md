# experiments/

Research harness — **not part of the shipped package**. Exploratory comparisons that inform
gated decisions about the core. Kept out of the package's dependency set on purpose (the package
stays lean: click/fastapi/pydantic/pyyaml/rank-bm25/uvicorn). Anything that proves out here gets
promoted into `src/` as its own slice, recorded in an ADR.

## semantic_vs_bm25.py — does semantic retrieval beat the BM25 baseline?

The comparison ADR-009 / ADR-012 require before promoting semantic retrieval. Compares three
retrievers over the **same status-gated chunks** the production core uses
(`docs/corpus-data.json`) against a labeled relevance set (`queries-labeled.json`):

- `bm25` — faithful BM25Okapi port of the production baseline
- `semantic` — `all-MiniLM-L6-v2` bi-encoder cosine (the Evidence Bundler pattern)
- `hybrid` — reciprocal-rank fusion of the two

Outputs `comparison-report.md` and `comparison-results.json`.

### Headline finding (2026-06-13)

Easy (corpus-vocabulary) queries tie. On **hard paraphrases**, BM25 collapses (MRR 0.49) while
**semantic is perfect (MRR 1.00)** — and semantic also admits a **clean cosine refusal threshold
(~0.30)** that raw BM25 score cannot. Hybrid helps neither. The current coverage gate wrongly
refuses 9/16 on-topic queries (the refusal-bias documented in ADR-012). **Recommendation:
promote semantic + a cosine refusal threshold next, not hybrid**, validated on a larger/real
corpus first. See `comparison-report.md` and ADR-014.

## Run it

Needs `sentence-transformers` (CPU; the `all-MiniLM-L6-v2` model is cached after first use).
Use any interpreter that has it — e.g. a fresh experiments venv:

```bash
python -m venv .venv-exp && .venv-exp/bin/pip install -r experiments/requirements.txt
.venv-exp/bin/python experiments/semantic_vs_bm25.py
```

Regenerate `docs/corpus-data.json` first (via `scripts/build_pages_demo.py`) if the corpus
changed, so the experiment runs over the current chunks.

### Reproduction note (2026-09-26)

The harness indexes and embeds `index_text` (section heading + verbatim span), the string
production indexes. Between ADR-016 and this note it indexed the body-only `text` field instead,
so a re-run would not have reproduced the recorded BM25 inputs. `tests/test_experiment_harness.py`
now checks the BM25 arm against `comparison-results.json` in CI. The semantic arm needs the
embedding model and has not been re-run since 2026-06-13; the headline above is directional (see
ADR-014's amendment and `plans/public-generative-rag-v2.md` §1.8).
