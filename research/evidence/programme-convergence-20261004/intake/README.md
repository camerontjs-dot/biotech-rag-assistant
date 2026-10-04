# Biotech evidence intake candidates — 2026-10-04

This package prepares append-only source nominations and candidate deltas for Evidence Room review. It contains **two references to existing A07/A08 nominations and three new delta candidates containing 13 records**. It does not compose an Evidence Room state, admit records, promote a collection, or count a review or publication as another physical experiment.

## Source-bound outcomes

| Lane | Existing subject | Preserved result | Intake treatment |
|---|---|---|---|
| A08, PR #47 / issue #42 | `17ebc301c9fa810d49c443d6d9919bbcad0e95d4` | `BOUNDED_CITATION_SPAN_EXPANSION_SUPPORTED` | Reuse the existing source-side `INTAKE.json`; closed unmerged at the unchanged head. The frozen/recomputed increase is **28 characters**, from 48 to 76; earlier prose saying 30 is corrected in the closure record. |
| A07, PR #48 / issue #43 | `8bebd572ca3628e3fc992c8cd0a3fb17cb2b69dc` | `SAME_SECTION_BODY_EXPANSION_NOT_SUPPORTED` | Reuse the existing source-side `INTAKE.json`; closed unmerged at the unchanged head. Authorized body remains 185 characters at 55:240; zero added. |
| PR #51 author corpus | `bf07ea3b16854830a9a2ec5a0c9725488bb02f17` | `APPARATUS_INVALID` at corpus materialization/freeze | Separate aggregate transport observations, three original failed/interrupted author attempts, failed mechanical freeze, and downstream semantic `NOT_RUN`. |
| PR #50 citation helper | `9685872827b37b55c981b88ad3177a2ed3b13533` | `NOT_QUALIFIED` | Keep machine contract probes and the independent engineering review in separate records. |
| CI proof and product | Proof `7196aec48378932e2dde235b560ddaff56a814dc`; product `bc457271bc9a29fbe5561dfcba6b3b398df09616` | Proof `SUPPORTED_FOR_PROMOTION`; product `QUALIFIED_READY_FOR_OPERATOR_PROMOTION` | Keep three hosted runs separate from two engineering reviews. The operator promotion gate remains. |

The A07/A08 source identities, hashes, inherited semantic-authority limits, and closure comments are in [existing-a07-a08-nominations.json](existing-a07-a08-nominations.json). Their result functions mechanically replayed the frozen observations. The inherited PR #20 semantic judgments remain `agent_llm`, moderate-confidence, `needs-audit`, without an independent human adjudicator; this intake work adds no semantic oracle.

## Why the new records are separate

[PR #51 candidate](candidate-deltas/pr51-apparatus-and-nonexecution.json) preserves 28 complete transport-schema-valid responses without treating that count as a valid corpus. The 44 authored rows cover only 33 unique planned slots, leaving 11 missing and 11 duplicated anchor slots. The unchanged materializer accepts 18 partitions and rejects 10. No complete cases/design/relations freeze exists. All semantic adjudication, comparison, reconciliation, assurance, qualification, and assessor implementation stages remain `NOT_RUN`; their scientific results are `UNKNOWN`. Earlier output-ceiling, context-window, and request-without-response attempts remain visible beside their later canonical responses. Reusing request bytes does not make two executions the same attempt.

[PR #50 candidate](candidate-deltas/pr50-independent-contract-review.json) preserves 118 passing maintained tests alongside 14 passing and 10 failing independent probes. Two material defects concern overlapping quote ambiguity and sentence boundaries that can omit a same-sentence condition; the leading-whitespace probe remains an additional documented limitation. Rejection applies to the exact original helper. It does not reverse the earlier single-case A08 observation. Public logs and review narratives have their own hashes; [published provenance](https://github.com/camerontjs-dot/biotech-rag-assistant/blob/4191e9b7809f76956330f0c01312ccdb09f8055e/research/evidence/citation-sentence-selection-review-20261004/provenance.json) distinguishes byte-identical copies from workspace-prefix transformations.

[CI candidate](candidate-deltas/ci-execution-and-review.json) records the predecessor run's three failing combined jobs plus successful parity, the proof run's Ruff failure plus ten successful independent jobs, and the product run's eleven successful jobs. The published review inspected all 26 job logs. The proof workflow remains failed overall while demonstrating that Ruff no longer suppresses the other evidence surfaces. Qualification and merge authority are recorded separately.

## Immutable receipt publications

Execution/product identities above remain distinct from the commits that append their review receipts.

| Publication | Receipt commit | Source directory |
|---|---|---|
| Corpus terminal | `7556badf6077bac2edd20f163faa5af0ef1b95d1` | [Corpus freeze](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/7556badf6077bac2edd20f163faa5af0ef1b95d1/research/evidence/semantic-control-memory-bounded-20261003/corpus-freeze-20261004/) |
| Citation review | `4191e9b7809f76956330f0c01312ccdb09f8055e` | [Citation review](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/4191e9b7809f76956330f0c01312ccdb09f8055e/research/evidence/citation-sentence-selection-review-20261004/) |
| CI review | `72711ba2f81b27e68033b287e0035ab8ad170a9a` | [CI review](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/72711ba2f81b27e68033b287e0035ab8ad170a9a/research/evidence/ci-independent-review-20261004/) |

[source-publications.json](source-publications.json) binds full trees, source prefixes, manifest hashes, and available terminal comments. Each candidate also binds its own relevant artifact hashes and source URLs.

## Evidence Room admission boundary

The inspected [Evidence Room #47 review](https://github.com/camerontjs-dot/the-evidence-room/issues/47#issuecomment-5975739356) qualifies the bounded append-only mechanism while retaining **MIXED / HOLD** for semantic admission. Its VE-NOM-02 finding specifically separates owner workflow observations from a later reviewer classification. These candidates preserve that distinction.

[structural-preflight.json](structural-preflight.json) records pure `validate_delta` checks using the inspected frozen intake implementation and 26-episode baseline. Passing those checks establishes schema/identity/lineage/privacy-shape compatibility in that bounded fixture. It does not establish semantic correctness, source admission, exhaustive deduplication against unseen deltas, or promotion. Current accepted delta identities must be rechecked before admission. The existing A07/A08 source nominations must not become second experiments.

## Current CAL and heading boundaries

[cal-status-reconciliation.json](cal-status-reconciliation.json) preserves the original CAL #189 explicit-negation falsification of #186 while recording the later bounded polarity successor, completed independent #204 review, and EB #131 `SUPPORTED_VERIFIED_SOURCE_CUSTODY_BEFORE_CAL`. The verified provenance result applies to the pinned EB → Contract B 1.2 → CAL chain. Direct caller `source_sha256` remains unverified, general natural-language authoring remains outside the supported V1 surface, and Biotech integration is `NOT_RUN`.

Biotech [#49](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/49#issuecomment-5976501663) remains open `NOT_RUN` for a separately qualified, explicit heading-semantic experiment. ADR-018 is unchanged. The apparatus terminal, citation rejection, CI qualification, and CAL successor do not authorize that experiment or reopen blocked Wave B.
