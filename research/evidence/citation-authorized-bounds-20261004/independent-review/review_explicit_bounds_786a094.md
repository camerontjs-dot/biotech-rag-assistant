# Engineering review of explicit authorized citation bounds

## Disposition

**No material defect found in the revised, explicitly bounded mechanical utility at `786a09421c95c55506a3e82f96006449e064b4d7`.** The content-equivalent published commit is `897e22827fe9848d460734f1b2432c6f6babc45d`. The reviewed tree is `4ff09a40a38c41a20d64d436ff67463750a254cd`. This disposition covers exact quote containment, global literal uniqueness, explicit integer offsets, unmodified source slicing, and the declared paragraph-break policy. It does not qualify automatic sentence extraction, caller authority, linguistic completeness, semantic support, or API/CLI integration.

The raw fresh frozen score is **49/51**. All **15 required exact selections** and **36 required safe refusals** occurred. The two raw failures are retained refusal-name expectation mismatches, explained below. They are not reclassified as passing tests, and no source or frozen expectation was changed to remove them.

The earlier automatic candidate remains rejected: its original frozen result is **30/32**, with paragraph crossing; the six separately labeled exploratory examples also reproduce abbreviation truncation and paragraph crossing. This new API has a different contract and cannot retroactively pass the automatic-selection expectations.

## Identity and review provenance

| Subject | Locally tested commit | Published content-equivalent commit | Exact git tree |
| --- | --- | --- | --- |
| Rejected automatic selector | `093fcd031138b8219722f4e9c888dec2d7ebc354` | `8ddd2a8969869be5e5dfe339b45087f1ee7e8803` | `d7a96fe4bae53f30dbdcf1f179b3710bd1a5b5cf` |
| Explicit authorized bounds | `786a09421c95c55506a3e82f96006449e064b4d7` | `897e22827fe9848d460734f1b2432c6f6babc45d` | `4ff09a40a38c41a20d64d436ff67463750a254cd` |

Published commit tree IDs and source/document SHA-256 digests were read from fetched git objects and verified against the locally tested subjects. The portable harness was rerun against a clean detached checkout of published `897e22827fe9848d460734f1b2432c6f6babc45d` and reproduced the same raw 49/51 result and 15-selection/36-refusal behavior. A dirty publication working tree was correctly refused by the harness; no dirty files were used for that reproduction.

Explicit-bounds implementation SHA-256: `e3c1198b900aa075edd2bf04575783419dc0de87d63ab2e640ed6309a5ae94d1`. Contract document SHA-256: `50bb6d702abc65583e339d1c05e9b97c583849d752863ddd7c2a790c9399c29e`. Fresh frozen probe SHA-256: `22460e1fe41a0b0a3875d15e56552ee473e1ad36ae80e771c51333699e4f8659`.

The fresh probes were frozen before this reviewer read the new implementation or its document. Inputs known beforehand were the announced API/outcomes, historical automatic-selector failures, and the author's notice that a single CRLF wrap is supported, which also mentioned an atomic paragraph regexp. That exposure is recorded in the frozen fixture. This is ordinary separate-context engineering review, not semantic adjudication, clean-room construction, or training independence.

## Frozen test interpretation

| Evidence | Result | Interpretation |
| --- | --- | --- |
| Required exact authorized selections | 15/15 observed | Exact caller offsets and text preserved; no punctuation inference or widening. |
| Required refusals | 36/36 observed | No missing-bound inference, repeated-quote resolution, invalid-range coercion, or paragraph crossing. All refusals have null span fields. |
| Raw exact outcome-name score | 49/51 | Two pre-documentation probes guessed a stricter refusal taxonomy than the published contract. |

The two mismatches are `missing_start_bound` and `missing_end_bound`. Each supplied only one endpoint and expected `bounds_required`. The actual result was `invalid_bounds` with null `text`, `start`, and `end`. The published outcome table explicitly reserves `bounds_required` for neither endpoint being supplied and assigns incomplete ranges to `invalid_bounds`; source lines 53–56 implement that rule. The initial API announcement did not specify this distinction, so the reviewer overconstrained an unspecified label. The meaningful safety behavior is a refusal with no inferred bounds in both cases. The raw fixtures, raw report and exact score remain unchanged. `explicit_bounds_adjudication.json` records the decision separately.

## What the evidence establishes

**Literal uniqueness is global and includes overlaps.** The new probes include `QA QA` within `QA QA QA`, `aba` within `ababa` with a second overlap extending outside the supplied span, and repeated quotes outside the selected range or in a different paragraph. Every case returns `ambiguous`. Narrow bounds cannot silently choose one globally repeated occurrence. Source lines 46–52 check quote presence and overlaps before considering bounds.

**The selected slice is precisely the caller's range.** Ordinary sentences, a middle sentence with neighbors, edge whitespace, decomposed Unicode, a preceding non-BMP character, accents, Greek text, single LF and single CRLF wraps all return the exact supplied slice and Python codepoint offsets. Full-span quotes and quotes touching either edge are preserved. Brackets, curly quotes, quoted punctuation and an unrecognized abbreviation no longer trigger boundary inference. They remain the caller's already authorized text. Source lines 55–65 enforce plain integer bounds, range validity, quote containment and exact slicing.

**Missing and invalid bounds refuse.** Neither supplied endpoint returns `bounds_required`. Partial endpoints, booleans, strings, floats, negative/reversed/empty/out-of-range intervals and intervals that omit any part of the unique quote refuse with null text and offsets. A missing, empty, whitespace-only, case-mismatched, or normalization-mismatched quote does not become a fabricated match. Quote presence/global uniqueness retain documented precedence over range checks.

**Paragraph limits are mechanical and declared.** LF, CRLF and CR blank lines, whitespace-only intervening lines including a nonbreaking space, and U+2029 cause `invalid_bounds` when present inside the selected range. A single LF or CRLF wrap is accepted. Paragraphs elsewhere in the supplied BODY do not invalidate a wholly contained authorized range. This is the declared representation-level policy, not a claim to recognize every possible paragraph convention in arbitrary source formats. The pattern is at source line 14 and is applied only to the selected slice at lines 61–63.

**The utility remains unconnected.** Source reference inspection found the new helper only in its defining module within `src`; the automatic `select_enclosing_sentence` and `sentence_spans` APIs are absent there. The implementation imports only standard-library modules and the project's existing Pydantic dependency. Project metadata requires Python >=3.11; review execution used Python 3.12.14. No provider call, package startup, source retrieval, external authorization action or GitHub write was performed by this reviewer. The parent reports the maintained 164-test suite and Ruff passing; those whole-suite counts are parent execution evidence, not reruns by this reviewer.

## Important precondition

A caller can authorize an incomplete or misleading span. This utility will return that exact range when its mechanical checks pass. It deliberately cannot determine whether the range forms a complete sentence, preserves every limiting condition, or supports an answer. The source docstring and document make this limitation explicit. Passing offsets from an unqualified automatic punctuation parser would restore the unresolved upstream failure; it would not convert this validator into a qualified sentence detector.

The same distinction applies to source authority. A heading or external string absent from the supplied BODY cannot be fetched or selected by this utility. Whether the supplied BODY and offsets should be authorized at all remains the caller's responsibility. This review gives no additional authority to headings, stale material, source statuses or semantic gates.

## Portable reproduction

Use `reproduce_review.py` with the corresponding frozen JSON files alongside it, Python >=3.11, and the repository's Pydantic dependency installed. The harness accepts arbitrary checkout and output paths and checks the exact expected tree, clean tracked files, implementation/document hashes, and probe hash before loading only the target module. It records the actual commit and command used.

```bash
python reproduce_review.py --probe-set authorized --checkout /path/to/checkout-at-897e228 --output /path/to/authorized-results.json
python reproduce_review.py --probe-set automatic --checkout /path/to/checkout-at-8ddd2a8 --output /path/to/automatic-results.json
python reproduce_review.py --probe-set automatic-extra --checkout /path/to/checkout-at-8ddd2a8 --output /path/to/automatic-extra-results.json
```

Each command intentionally exits **1** when any raw expectation fails. Expected raw results are 49/51, 30/32 and 0/6 respectively. That exit status preserves the evidence; the separate explicit-bounds adjudication explains the two non-material label mismatches. The automatic-extra set is post-inspection exploratory evidence and is never included in the frozen 32.

Local command provenance and the original adapters remain in the original records. The portable publication run is `portable_authorized_publication_report.json`; the automatic reproductions are `portable_automatic_report.json` and `portable_automatic_extra_report.json`.

## Evidence files

- `review_093fcd0.md`: rejection review for the original automatic selector.
- `preimplementation_probes.json`, `frozen_candidate_report.json`, `postfreeze_probes.json`, `postfreeze_candidate_report.json`: unchanged automatic-selector evidence.
- `explicit_bounds_preimplementation_probes.json`, `explicit_bounds_freeze_record.txt`, `explicit_bounds_candidate_report.json`: frozen new-contract inputs, exposure record and raw results.
- `explicit_bounds_adjudication.json`: separate explanation of the two outcome-name mismatches.
- `reproduce_review.py`: portable harness for all three probe phases.
- `publication_identity_mapping.json`: verified local/published commit and tree equivalence.
- `review_manifest.json`: SHA-256 identities for the review deliverables.

No recommendation to wire this helper into a consumer or promote semantic behavior is made by this review. Such a change must bring independently justified bounds and preserve existing source and support gates.
