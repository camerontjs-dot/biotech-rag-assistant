# Reproduce the citation-selection engineering review

This folder preserves evidence for two different contracts. The automatic selector failed; the explicit-bounds validator received a limited mechanical qualification. Read `review_093fcd0.md` and `review_explicit_bounds_786a094.md` before interpreting counts.

## Portable harness

`reproduce_review.py` requires Python >=3.11, Git, and the project's Pydantic dependency. Keep it beside the three JSON probe sources or pass `--probe-directory PATH`. It accepts `--checkout PATH` and `--output PATH`; no workspace path is hardcoded.

Use a clean checkout at published `8ddd2a8969869be5e5dfe339b45087f1ee7e8803` for `--probe-set automatic` or `--probe-set automatic-extra`. Use published `897e22827fe9848d460734f1b2432c6f6babc45d` for `--probe-set authorized`. Local equivalent commits and all verified tree/source identities are recorded in `publication_identity_mapping.json`.

```bash
python reproduce_review.py --probe-set authorized --checkout /path/to/explicit-checkout --output /path/to/authorized-results.json
python reproduce_review.py --probe-set automatic --checkout /path/to/automatic-checkout --output /path/to/automatic-results.json
python reproduce_review.py --probe-set automatic-extra --checkout /path/to/automatic-checkout --output /path/to/automatic-extra-results.json
```

Expected raw scores are 49/51, 30/32 and 0/6. The harness deliberately exits 1 on any raw mismatch. Do not treat the two documented outcome-name mismatches in the authorized set as unsafe selection: all 15 required exact selections and 36 required refusals occurred. Conversely, do not erase or relabel those two raw mismatches. `explicit_bounds_adjudication.json` explains the distinction.

The original `run_*_candidate.py` scripts preserve the local command provenance and hardcoded original targets; use the portable harness for new reproduction. Probe source hashes are checked before execution. No provider clients, API, CLI or semantic checks are invoked.
