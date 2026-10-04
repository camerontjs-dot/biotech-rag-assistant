# Biotech programme convergence — 2026-10-04

This is an immutable coordination snapshot of the completed cleanup and bounded reviews. GitHub issues, pull requests, source commits and execution receipts remain authority. This record is not another experiment or a continuously maintained dashboard.

At the **2026-10-04 04:30:22 UTC** read, the original 20 open PRs and five open issues had converged to **one open Draft PR (#45) and two open issues (#39 and #49)**. Nineteen original PRs were closed unmerged and three issues were closed completed. Branches and historical evidence were retained. The archival PR used to publish this snapshot is a separate completed coordination record.

## Main and promotion

| Identity | Value |
|---|---|
| Current main | `cd9ba8bc4351ac0cb4cf022ec1ddf449671454c3` |
| Main tree | `f18297d7aac560d3efbde525c3b3776c5e091490` |
| Product merges in this pass | 0 |
| Qualified CI candidate | PR #45, `bc457271bc9a29fbe5561dfcba6b3b398df09616` |
| CI promotion status | `QUALIFIED_READY_FOR_OPERATOR_PROMOTION` |

The [explicit PR #45 operator gate](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/45#issuecomment-5971207812), also recorded on [issue #40](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/40#issuecomment-5971207277), remains effective. No protected branch rule or required status context was observed; that does not waive this authority boundary. The concrete pending decision is authorization for a normal merge of the exact qualified #45 commit, after rechecking main and head for drift. The post-merge SHA/tree and maintained checks would then be recorded.

## Completed lanes

| Lane | Result and consequence |
|---|---|
| CI #45/#46 | Independent review inspected all 26 decoded job logs across the inherited run, proof run and product run. The proof kept Ruff red with 298 findings while all 10 other jobs executed and passed. Product #45 passed all 11 jobs. #46 is closed unmerged with an appended review. #45 remains Draft at the operator gate. |
| A08 #42/#47 | `BOUNDED_CITATION_SPAN_EXPANSION_SUPPORTED`. The same authorized BODY sentence expands the quote from 48 to 76 characters: **28 added**, correcting earlier prose claiming 30. No new packet member or heading. Issue #42 is completed; #47 is closed unmerged at its original head. This inherits #20's N/P semantic judgment, with moderate confidence and needs-audit status; it is not fresh independent semantic adjudication. |
| Citation product #50 | `NOT_QUALIFIED`. All 118 maintained tests pass, but the independent contract suite returns 14 pass / 10 fail. Overlapping repeated quotations can be treated as unique, and abbreviations can truncate an enclosing sentence before a limiting condition. The original implementation and author tests were not changed. #50 is closed unmerged; its failure does not undo the earlier bounded A08 observation. |
| A07 #43/#48 | `SAME_SECTION_BODY_EXPANSION_NOT_SUPPORTED`. The complete authorized Daily check BODY was already the 185-character aperture at document offsets 55:240. Zero characters added; the missing daily-check scope remains absent. Issue #43 is completed; #48 is closed unmerged at its original head. |
| Semantic control #41/#51 | `APPARATUS_INVALID` during structural materialization/freeze. All 28 partitions have complete transport-schema-valid responses, but 44 case rows cover only 33 unique planned case slots. Eleven slots are missing and eleven anchors are duplicated. The unchanged frozen materializer accepts 18 partitions and rejects 10. #41 is completed and #51 closed unmerged with append-only failure evidence. |
| Predecessor #38 | Original timeout remains `APPARATUS_INVALID` at unchanged head. Closed only after #51 published its own separately identified terminal result. |
| Heading successor #49 | `NOT_RUN`. The failed semantic-control candidate supplies no qualification for a heading-grant experiment. ADR-018 remains active. |

The CI [independent review](https://github.com/camerontjs-dot/biotech-rag-assistant/blob/72711ba2f81b27e68033b287e0035ab8ad170a9a/research/evidence/ci-independent-review-20261004/review.md), citation [independent review and counterexamples](https://github.com/camerontjs-dot/biotech-rag-assistant/tree/4191e9b7809f76956330f0c01312ccdb09f8055e/research/evidence/citation-sentence-selection-review-20261004), and corpus [terminal receipt](https://github.com/camerontjs-dot/biotech-rag-assistant/blob/7556badf6077bac2edd20f163faa5af0ef1b95d1/research/evidence/semantic-control-memory-bounded-20261003/corpus-freeze-20261004/TERMINAL.json) preserve the full evidence and limitations.

### No valid corpus freeze exists

The author subject remains `bf07ea3b16854830a9a2ec5a0c9725488bb02f17`, tree `cdb440064c4ec469aa7bc48d8bfc7fd3e5185a91`. The appended failure publication is `7556badf6077bac2edd20f163faa5af0ef1b95d1`, tree `9a5baa2f1c17a81ef2eb80be3258dbca61af5d00`.

The canonical attempt map was selected mechanically, without comparing answer quality. Earlier context cutoff, output-cap and no-response attempts remain separate. Raw request/response reconstruction, expected slot assignments, the unchanged materializer and independent identifier-only checks establish the structural failure. The complete `cases.jsonl`, sealed `design.json` and `relations.json` required by the frozen contract could not be validly materialized; their valid-freeze hashes are null.

The terminal receipt SHA-256 is `9356adffb1c0e24234be6771f5367471ed9705d2a2381e531c82407b77685808`. The custody manifest SHA-256 is `f1e1b898eb264efa4ed2e9aac78a0aa1263a67f4ef2333f92b6659e331f03283`. These identify a **failed freeze receipt**, not a qualified corpus.

A, B and blind C were **NOT_RUN**. No adjudicator identities, outputs, agreement denominator, disagreement ledger, reconciliation, semantic design reveal, mutation/invariance assurance or assessor qualification exists. Scientific outcomes remain UNKNOWN. No new provider or semantic calls occurred in this pass. **Wave B remains LOCKED**; no new TEST or PROSPECTIVE execution occurred.

## Closed surfaces and historical lineage

All closure comments, exact original and final heads/trees, classifications and successor links appear in [surface-ledger.json](surface-ledger.json). Original API closure receipts are in [original-closure-receipts.json](original-closure-receipts.json). [historical-lineage.json](historical-lineage.json) keeps historical qualifications and later source corrections distinct.

| Original surfaces closed | Reason |
|---|---|
| PR #3 and #44 | `PLANNING_COMPLETE`; ongoing execution belongs to #39 and its identified lanes. |
| PR #4 | `SUPERSEDED` by the separately frozen v2.1 benchmark; the downstream #6 discrimination failure remains preserved. |
| PR #7 and #8 | Terminal benchmark and retrieval-selection evidence. DEV and TEST challenger gains remain recorded, while preregistered promotion gates retained BM25. |
| PR #9 and #10 | `SUPERSEDED` parallel prototypes. The programme follows #11/#12; the retired prototypes are distinct implementations, not failed or byte-equivalent copies. |
| PR #11–#15 | Completed packet, generation, export, pressure and structured Wave A milestones. Original qualified commits, manifest repairs, failures and replays remain distinct. |
| PR #19 | Completed accepted heading-authority record. `ACCEPTED_EP1_HEADING_AUTHORITY_EXCLUSION` continues through immutable references after closure. |
| PR #38, #46, #47, #48, #50 and #51 | Terminal apparatus, proof, positive/negative research, rejected implementation and failed-freeze evidence described above. |
| Issues #41, #42 and #43 | Completed at their recorded terminal boundaries. Issue #39 remains the active programme owner. |

Only #46, #50 and #51 received new append-only receipt commits in this pass. Their original execution/implementation identities remain separate from publication identities. No branch was deleted and no history rewritten. BM25 remains the experimental retrieval control; the grounding findings do not authorize reopening retrieval selection.

## Live CAL reconciliation

The prompt's last-known CAL state was overtaken by a separately qualified bounded successor. The historical #189 negation falsifier of #186 remains intact. The #191 polarity successor and qualification lineage #194/#199/#201 lead to product `64b6c7702696c851057c1cf0b2c105b1c81db543`.

Pressure #203 records `PRESSURE_SUPPORTED_NO_CRITICAL_FAIL_WITH_DOCUMENTED_LIMITS`; the closed [independent #204 review](https://github.com/camerontjs-dot/claim-audit-lab/issues/204#issuecomment-5975316839) supports that bounded result while retaining `V1_BOUNDARY_DECISION_REQUIRED`. The 26 real-claim authoring refusals yielded zero semantic decisions, so they do not demonstrate general natural-language semantic coverage.

[Evidence Bundler #131](https://github.com/camerontjs-dot/evidence-bundler/issues/131#issuecomment-5976059899) now records `SUPPORTED_VERIFIED_SOURCE_CUSTODY_BEFORE_CAL` for the pinned EB → Contract B 1.2 → CAL chain. Direct caller `source_sha256` is still not verified custody. **Biotech integration remains NOT_RUN** and was not authorized or executed by this pass. [The full reconciliation](intake/cal-status-reconciliation.json) records exact identities, observed source status and inspection limits.

## Evidence Room candidates

The byte-preserved [intake package](intake/README.md) contains **three new candidate deltas with 13 records**, plus references to the two existing A07/A08 source nominations:

| Delta | Records | Treatment |
|---|---:|---|
| [#51 apparatus and nonexecution](intake/candidate-deltas/pr51-apparatus-and-nonexecution.json) | 6 | Aggregate transport completion; three preserved failed/interrupted attempts; structural freeze failure; downstream semantic nonexecution. |
| [#50 machine evidence and independent review](intake/candidate-deltas/pr50-independent-contract-review.json) | 2 | Probe observations and engineering rejection remain separate. |
| [CI execution and review](intake/candidate-deltas/ci-execution-and-review.json) | 5 | Three physical hosted runs and two qualification judgments remain separate. |

Pure structural preflight against the inspected frozen `evidence-intake-delta/v0` implementation passed all three deltas and 13 records. This does not establish semantic admission or global deduplication against the complete current accepted-delta inventory. No Evidence Room collector, platform stage, composition, admission or promotion occurred. The preserved candidate status label `STAGED_NOT_ADMITTED` refers to local preparation and explicitly records `stage=false`.

The intake manifest SHA-256 is `ebeb5677861c0c54870cc399ce414b2e89380b40822d6065307870a7b5e4aabe`. Evidence Room #47's mechanism remains qualified and its separate semantic-admission state **MIXED / HOLD**. Later review must recheck baseline and accepted delta identities, preserve source-owner observations versus reviewer interpretation, and reuse existing A07/A08 nomination identities. Hash-only private references are not claims that their raw bytes were inspected or published.

## Remaining ownership and next steps

| Open surface | Work it owns |
|---|---|
| Draft PR #45 | Qualified one-file CI product candidate awaiting explicit operator promotion. |
| Issue #39 | Active programme coordination; prospective author-output contract successor and a separate citation implementation successor. |
| Issue #49 | Useful unresolved heading-grant question, still blocked and NOT_RUN. |

The smallest immediately ready product action is operator promotion of CI #45. The smallest citation successor must reject overlapping repeated matches and establish an explicit conservative sentence-boundary policy, then independently qualify a separately identified candidate against the preserved probes. It must retain authorized BODY/source offsets and the existing retrieval and semantic boundaries.

The next research mechanism must prospectively enforce the already frozen case/design/relation assignments at the author-output boundary and qualify that apparatus before a new execution. The failed #51 candidate must not be relabeled or re-authored in place. #49 requires an adequate semantic route and a separate preregistered one-factor protocol before execution; it does not change ADR-018 merely by remaining open.

Every requested handoff item, including explicit nonexecutions, is represented in [convergence.json](convergence.json). The outer [SHA256SUMS](SHA256SUMS) binds this snapshot and the nested byte-preserved intake package. Git commit/tree identity is supplied by the archival publication and its closure receipt, avoiding self-referential commit hashes inside these files.
