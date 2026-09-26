# controlled-docs-v2 — synthetic controlled-document benchmark

Synthetic data only. No real organizations, products, persons, sites, or values attributed to real regulations or guidance. No text copied from private product content, private repositories, employer documents, or client material. Layout, gold schema, and aperture conventions follow public benchmark practice; all names and text are original.

## Runtime vs evaluator split

- Runtime (may be mounted): `corpus/`, `cases/dev_cases.jsonl`, `cases/test_cases.jsonl`, `adversarial/corpus/`, `adversarial/cases.jsonl`.
- Evaluator-only (never mounted into a runtime): `evaluator_only/` (gold spans, families, relationships, lexical overlap), `adversarial/evaluator_only/`.
- `PROSPECTIVE` cases are sealed outside the repository; only their SHA-256 is committed in `freeze_receipt.json`.

## Layout

Per plans/public-generative-rag-v2.md Appendix A.1. Gold offsets use `offset_unit: python_char`; every `span_text == text[char_start:char_end]`. Source hashes are computed from final bytes after all edits.

## Counts

- Documents: 42 retrievable, 14 superseded, 4 drafts, 4 obsolete.
- Cases: 40 DEV, 80 TEST committed; ~30 PROSPECTIVE sealed.
- Families: {"B01": 10, "B02": 12, "B03": 8, "B04": 11, "B05": 8, "B06": 8, "B07": 5, "B08": 10, "B09": 10, "B10": 14, "B11": 8, "B12": 6, "B13": 5, "B14": 5}

## Deviations

None. Generated output was not hand-edited. Any future corrections create `controlled-docs-v2.1`; the frozen tree is immutable.

## Provenance

Generator: `controlled-docs-v2-generator 0.1.0-local`. Seed: 42. As-of: 2026-09-26. Configuration hash: `sha256:1b4ef32fd1eda900046313deb67b5c03969b99d56ae35abcaf4cade932100f46`. No filesystem paths, prompts, or local configuration are committed.
