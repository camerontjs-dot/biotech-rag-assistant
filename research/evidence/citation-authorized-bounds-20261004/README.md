# Citation authorized-bounds candidate: engineering evidence

This publication preserves both the failed automatic selector and the successor's narrower contract. It supports review of draft PR #53 under programme issue #39. It does not change maintained callers or qualify answer support.

## Outcome

| Object | Evidence | Disposition |
| --- | --- | --- |
| Historical PR #50 | Original source, tests and counterexamples retained byte-for-byte under `tests/fixtures/citation-span-selection-pr50` | `NOT_QUALIFIED`; closed and unmerged. |
| First automatic successor, published `8ddd2a8969869be5e5dfe339b45087f1ee7e8803` | 30/32 frozen separate-review probes; 0/6 additional exploratory probes | Rejected: paragraph crossing and abbreviation truncation remain. Its 181 passing implementation tests did not establish the claimed boundary. |
| Explicit authorized bounds, published `897e22827fe9848d460734f1b2432c6f6babc45d` | 164 project tests on Python 3.11, 3.12 and 3.13; fresh review observes all 15 required exact selections and 36 safe refusals | No material defect found in the mechanical contract. Raw exact-label score remains **49/51**. |

The two raw explicit-bounds mismatches are preserved reviewer expectation errors: an incomplete endpoint pair was expected to return `bounds_required`, but the documented contract correctly returns `invalid_bounds`. Both refuse with null text and offsets. The frozen expectations and raw reports remain unchanged; `independent-review/explicit_bounds_adjudication.json` records the separate interpretation. The portable harness intentionally retains nonzero exit status for each raw mismatch.

## Supported contract and limits

`select_authorized_span()` requires externally supplied bounds and a globally unique exact quote. It checks overlapping occurrences, plain integer offsets, full quote containment and the declared paragraph policy, then returns the exact Unicode source slice. It does not infer a sentence boundary when bounds are absent.

The caller remains responsible for source authority and the correctness and completeness of its bounds. An incomplete caller-authorized range can pass these mechanical checks. Passing an unchecked automatic parser's offsets would reintroduce the unresolved upstream problem. No API/CLI consumer, retrieval policy, heading authority, source status or semantic gate is changed.

## Reproduction and identity

Read `independent-review/README.md` for portable commands and exact checkout requirements. That folder retains the original probe sources, freeze records, exposure statement, raw results, reviews, identity checks and reproduction harness. Its `review_manifest.json` verifies the copied review files.

Publication packaging: the original five Python evidence files now have `.txt` appended, preserving every byte. `independent-review/published-paths.json` maps the original manifest names to their stored paths. The active `reproduce_review.py` is a separately formatted copy of the original portable harness. `publication-formatting-check.json` verifies identical non-import syntax trees and the same import set, all 25 original artifact hashes, and reproductions of 30/32, 0/6 and 49/51. Use this active copy for the README commands; restore archived adapter filenames into a separate temporary directory only when reproducing their original command provenance.

The first evidence publication at `15b1055abcddd08b645a6b52f623bb9501483182` failed [CI run 37207175942](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/runs/37207175942) on 12 lint style findings in the newly copied review scripts. Its test, compile and corpus steps were skipped in all three Python jobs; Pages parity passed. That result remains visible. The packaging correction changes neither lint rules nor candidate implementation, tests, frozen probes or raw outcomes.

`publication-map.json` maps local tested commit objects to GitHub-published objects with identical trees. GitHub commit metadata differs; equality is established by tree identity and file hashes, not by treating distinct commit names as interchangeable. The original local commit-object bytes are retained and reproduce their local commit hashes with `git hash-object -t commit`.

`hosted-ci-source.json` records the physically inspected source-publication CI run: each of the three Python jobs completed 164 tests, lint, compilation and corpus validation; Pages parity completed 42/42 checks. The documentation/evidence publication does not alter the reviewed implementation or tests. Its latest hosted CI receipt belongs in the PR conversation so recording that receipt does not create a self-referential new build.

This is ordinary separate-context engineering review with declared historical exposure. It is not clean-room semantic adjudication, training independence, or a provider-backed experiment.
