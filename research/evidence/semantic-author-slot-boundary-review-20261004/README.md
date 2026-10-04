# Prospective authoring boundary: engineering review and local handoff

Programme [#39](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/39), draft [PR #54](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/54). This evidence supports a research-infrastructure candidate and the next local runtime check. It is not a new authored semantic corpus or an assessor result.

## Exact reviewed source

Published source: `513cf0629b20a8d876e161f32f8bc6c6549e2012`.

Tree: `6428495c4f3b373cd07bdebcc7916834c157da3f`.

Wrapper SHA-256: `74e16e97341bb90d8845ba9f7bd78c03257b97ec79ff6a575b299ca7d3f97450`.

The local reviewed commit is `d1b256347d320e6268506b00978168c2d32b65ce`. `publication-map.json` records the three local-to-published tree-equivalent objects and all source, test and protocol hashes. Their different commit metadata is not treated as identical. The original local commit-object bytes are included and reproduce their local commit hashes.

## Problem and resulting behavior

The unchanged #51 terminal record contains 44 returned case rows but 33 unique assigned case slots, 11 missing slots and 11 duplicate occurrences. Generic schema compliance did not establish exact assignments or a valid corpus. The new boundary derives all 28 components, 44 case/design slots and 16 relations from the unchanged #30 design and #38 partition authority.

Compact positional schemas bind every assignment. The wrapper independently checks the plan, exact references, source spans/hashes, unique opaque identities, ordering, raw-to-materialized conversion, per-call acceptance and the unchanged full corpus gate. It requires an explicit new runtime configuration and a published prospective request freeze; then a canary and one attempt per author partition in strict order. All 11 retained transport artifacts and the boundary receipt are checked against their frozen relationships. Final corpus commitments include the canary and every author receipt.

No old #51 response is repaired or reused. Failed or interrupted execution stops the new run. An apparently complete set of rows cannot substitute for a valid full corpus freeze.

## Failures found and preserved

The first separate successor review returned **6/12** on the focused probe set. Six corruptions still permitted another fake request: edited materialization plus its edited hash, altered captured response text, missing model discovery, changed discovered digest, missing send marker, and contradictory boundary identity/stage metadata. These failures are retained in `independent-review/first-subject-probes.json` and `first-subject-findings.md`.

The final source returns **12/12** on the same probes. Every previously accepted corruption stops before any next fake HTTP action. This result is recorded separately; earlier failure outcomes are unchanged. The public text/JSON projections replace only the ephemeral scratch prefix, with exact original and published hashes recorded in `independent-review/FILE-MAP.json`. A nested engineering review also reproduced and verified fixes for symlinked output escape and a declared source root differing from loaded execution source. Its original minimal counterexample receipts remain in this folder.

The materialization correction protects evidence consistency: the first implementation already rebuilt final corpus prose from raw responses. The reproduced flaw allowed contradictory stored materialization to remain accepted; it did not demonstrate replacement of final raw-derived prose.

## Verification

| Evidence | Observed result and scope |
| --- | --- |
| Initial complete new suite | 17 passed before the later narrow custody corrections; see `biotech-authoring-tests-final.txt`. |
| Canonical-materialization correction | Two affected tests passed, including the complete 28-partition fake-runtime pipeline; see `biotech-authoring-canonical-check-tests.txt`. |
| Retained transport correction | Four targeted tests passed in 12.424 seconds, including 20 artifact/metadata corruptions and a false runtime digest with consistently edited hashes; see `biotech-authoring-transport-custody-tests.txt`. |
| Separate focused review | Same probes: first 6/12, final 12/12. Structural tokens and fake HTTP only. |
| Final full hosted controls | Dedicated workflow runs all 20 new plus 33 inherited structural tests on Python 3.11, 3.12 and 3.13, with frozen preparation checks and compile steps independent of the lint job. The exact final run receipt is recorded in #54 after completion. |
| New source lint | Both new Python files pass Ruff; the dedicated workflow checks them without changing inherited lint rules. |

The inherited research branch has 298 pre-existing full-repository Ruff findings. [Initial source CI 37207563378](https://github.com/camerontjs-dot/biotech-rag-assistant/actions/runs/37207563378) stops at those lint findings; ordinary test, compile and corpus steps are skipped, while Pages parity succeeds. That result is not a test failure or a passing test receipt. The dedicated new workflow supplies actual structural execution separately. It does not waive or repair frozen inherited debt, promote #45, or make the aggregate legacy CI green.

## Review provenance and limits

Read `independent-review/README.md` and `acceptance-plan.md`. The twelve acceptance areas were frozen before reading the successor; the focused probe executable subsequently tested the concrete source risks. This is ordinary separate-context engineering review with historical failure exposure. It does not establish blind semantic adjudication, human agreement, or model/training independence.

All execution in this bundle uses structural tokens and fake HTTP. Real provider calls are **zero**. A/B/C, semantic assessor, reducer, heading-grant #49, Wave B and Biotech integration remain unrun. Local hashes establish consistency relative to trusted frozen inputs; they cannot authenticate a provider after coordinated rewriting of every artifact and its external authority.

Local runtime formatter compatibility, capacity, untruncated request handling, privacy, synthetic provenance and historical separation require their own actual evidence. Reported prompt counts alone do not prove untruncated input. Even a complete structural freeze retains `NOT_READY_PENDING_CONTEXT_AND_CUSTODIAN_REVIEW` and `UNKNOWN_SEPARATE_LOCAL_EVIDENCE_REQUIRED` until that evidence exists.

## Next action

Use [the pinned local task](../../../plans/local-authoring-task-20261004.md) and [programme handoff](../../../plans/biotech-github-local-handoff-20261004.md). The actual authoring CLI is documented in [the protocol](../../semantic-author-slot-boundary-v1-protocol.md). The local supervisor must preserve the EB thread and its processes, publish the full prospective freeze before the canary, and stop at the complete structural corpus freeze or the first durable failure.

Original review scripts are archived with `.txt` appended to preserve their exact bytes as evidence. `independent-review/FILE-MAP.json` maps original names to stored paths and hashes; `MANIFEST.json` verifies the published files. To reproduce, copy the archived probe to a separate temporary `.py` file, use `--subject` pointing to the exact source snapshot and `--result` pointing to a new result file, and follow the command in the final review. Never overwrite the preserved reports with a reproduction.
