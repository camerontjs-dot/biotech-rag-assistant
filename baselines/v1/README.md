# Baseline V1

The before-state for [`plans/public-generative-rag-v2.md`](../../plans/public-generative-rag-v2.md), recorded in Slice 0. It describes the package, corpus, and public demo at `main@40de3cdcd98973b0e3a1c91d6ac114bc62857c04`. Nothing under `src/`, `examples/`, or `docs/` changed while it was recorded.

## Files

| File | What it holds | How it is checked |
|---|---|---|
| `baseline.json` | package source digest, corpus and chunk manifests, retrieval config, hashes of the evaluation fixtures and demo files, trust and natural-language suite results, demo chip outcomes, and the recorded ADR-014 headline | `python scripts/record_baseline.py --check`; the corpus section also by `tests/test_baseline_v1.py` |
| `near-miss-probes.json` | the plan's §1.8 probes: current behavior plus the disposition v2 should produce | `tests/test_baseline_v1.py` |
| `latency.json` | in-process timings on the recording machine | not checked; machine-dependent |
| `ux/*.png` | the public demo before any v2 work | not checked |

## Identities

| Object | Identity |
|---|---|
| Git tree `src` at the base commit | `76c0dae0087283a2e063183571f0a2456b8c19dc` |
| Git tree `examples/synthetic-controlled-docs` | `243f3ce350701a83fa0e50bc30f28080da31597b` |
| Git tree `docs` | `3f7a3b8f74da35a4801220d969932d11ec7acda4` |
| Package source digest | `sha256:9503578742b11644d11d4c7ae4aa09b7eb3d3d2d9810b269a931da1691d80688` |
| Corpus manifest (10 documents: 8 retrievable, 2 excluded) | `sha256:7b427aefdfcd11b8097298fd6c7c6ff006c5e7647ebcde07c8e22696d46f6f24` |
| Chunk manifest (18 chunks) | `sha256:31b91856f285e6468c9b04e9ad51c2ba723626cda4da9e3a4f93fc8647471dc5` |
| Retrieval config (`bm25`, `top_k` 5, `score_floor` 0.0, `min_top_coverage` 0.6) | `sha256:f9e784a81b4d0147e7734e975d19bfd6ff6b531c77db7eebb12325c46f74672c` |
| `baseline.json` | `sha256:dcdfc1dc7ee1eab1ad955532e36b5fb3ce5a915aee8a0be38ddd50085cea718e` |
| `near-miss-probes.json` | `sha256:31d5e401ba41219abfafa46a8ac1227b829131f741cc2916b652828b3e593be3` |

The hashing recipes are written into `baseline.json` under `recipes`.

## Recorded behavior

- Trust suite: pass, 24/24. Natural-language suite: pass, 13/13.
- Static demo parity: 40/40 (`python scripts/build_pages_demo.py`), and regenerating the demo reproduces the committed `docs/` files byte for byte.
- Demo chips: "env excursion response", "current approved version", and "balance calibration" answer; the obsolete-document trap and the off-topic chip refuse.
- ADR-014, as recorded on 2026-06-13 and not re-run: hard-set MRR is 0.49 for BM25, 1.00 for semantic, and 0.83 for hybrid; the coverage gate wrongly refuses 9 of 16 on-topic queries. The harness indexes `index_text` again, and `tests/test_experiment_harness.py` checks that its BM25 arm reproduces the recorded values. The semantic arm has not been re-run.

## Known gaps this baseline pins

- **Near-miss questions.** 4 of 6 near-miss probes are answered with passages that do not state the fact asked for, and 3 of those score above both supported controls. v2 should report them as `not_stated`.
- **No numbers in the retrievable corpus.** No Approved or Effective chunk contains a digit. The only number in the corpus is the "96 hours" in Obsolete SOP-QA-009. Every quantity question against v1 is therefore a near-miss or a refusal by construction; corpus v2 (plan Appendix A) adds explicit quantities.
- **Ordering.** For the "env excursion response" chip, rank 1 is the SOP's purpose statement (BM25 score 13.02), rank 2 is the passage that describes the response (3.98), and rank 3 is a water-system passage that shares "action limit excursion" (3.49). This is the kind of case the Slice 3 reranking arm tests.
- **The demo trap refuses at the coverage gate.** BM25 does return a passage for the sterility question, an unrelated gowning passage with coverage 0.00, and the lexical gate refuses it.

## Latency on the recording machine

Linux x86_64, Python 3.11, in-process and warm, no HTTP transport; 44 distinct questions, 30 repeats each.

| Operation | p50 | p95 |
|---|---:|---:|
| Build the index (18 chunks) | 0.517 ms | 0.673 ms |
| Retrieve | 0.087 ms | 0.136 ms |
| Retrieve + extractive answer | 0.111 ms | 0.168 ms |

## Reproduce

```bash
python scripts/record_baseline.py --check
python scripts/build_pages_demo.py
python -m pytest tests/test_baseline_v1.py tests/test_experiment_harness.py
```

The screenshots were taken with headless Chromium at 1280×900 in the light color scheme, with `docs/` served by `python -m http.server`: after clicking the "env excursion response" chip, after clicking the "obsolete-doc trap" chip, and after opening the held-out document from that refusal.

## Limits

This baseline records behavior on a synthetic 10-document corpus. It is not a quality or validation claim. Once later slices change the package, `--check` is expected to fail; record `baselines/v2` instead of editing this directory. The v1 corpus itself stays frozen, and `tests/test_baseline_v1.py` fails if it changes.
