---
title: "Frozen qualifier ledger reducer qualification"
domain: "ai-systems"
type: "lab-report"
status: "completed"
source: "Single decisive run and frozen scorer"
tags: ["offline", "grounding", "qualification", "falsification"]
updated: "2026-09-30"
lab_report_id: "2026-09-30-qualifier-grounding-offline-qualification-v1"
study_type: "confirmatory"
decision_sentence: "Preserve and reject qualification of this frozen reducer."
hypothesis: "A pure reducer satisfies every frozen ledger control without an oracle dependency."
primary_metric: "Exact per-control contract match; all controls required."
unit_of_analysis: "Assessment-ledger decision and preregistered paired relation"
n: 28
primary_independent_factor: "Independently implemented reducer"
disposition: "reject"
bounded_disposition: "FALSIFIED"
next_experiment: "qualifier-grounding-offline-qualification-v2; NOT_RUN"
---

# Frozen reducer falsified

The single decisive run returns **FALSIFIED**. Five controls match exactly and 23 disagree. All nine preregistered pair relations hold, but no pair has two fully matching endpoint controls. The relation results do not override per-case failures. No reducer repair or repeat of the fixed controls occurred.

## Candidate and aperture

- Branch: `research/qualifier-grounding-offline-qualification-v1`.
- Frozen commit: `10d17b3c56f54fca828c25c49de948051933733e`.
- Frozen tree: `48a1592a5f3b2e5d784115f8c834f34e879e5d2b`.
- Reducer SHA-256: `a90221d3ad85ebd647e904ab40c5773b0495855c6ca8a654c0a4c4d5ceac9ab8`.
- Clean freeze: `2026-09-30T17:21:22.036284+00:00`; first reveal: `2026-09-30T17:22:32.360199+00:00`.
- Contamination status: `NO_FORBIDDEN_CONTENT_EXPOSURE_OBSERVED`. This is grounded in the recorded aperture and implementation-owner declaration, with no separate human attestation.
- Read aperture and pre-freeze choices: [IMPLEMENTATION.md](IMPLEMENTATION.md). Exact identity and environment: [CANDIDATE.json](CANDIDATE.json), [REVEAL.json](REVEAL.json).
- Live starting branches matched PR #22 commit/tree. All supplied hashes, 12 normative frozen files, 31 receipt-frozen files, and pinned predecessor custody passed.
- The frozen preparation package remains unchanged and still records its original designed / NOT_RUN predecessor state. This directory carries the completed successor experiment.

## Apparatus and observations

Fourteen implementation-local tests and targeted lint passed before freeze. The frozen apparatus passed its direct preregistration check and all 16 selftests. The first selftest collection error was an import-path failure, preserved and repaired without changing any source or frozen authority. [Apparatus checks](apparatus-check.json), [selftest receipt](apparatus-tests.json), [full freeze verification](full-freeze-check.json).

The actual frozen Git source was compiled and invoked exactly 28 times. The runner denied file, network, process, environment mutation, and directory-change access during reducer execution; zero forbidden events were observed. Decisions were persisted and hashed before scorer import. [Execution receipt](decisive-run.json), SHA-256 `40bc936915f22d80eff51ae131d02632f5a995be0d5d304c15ccb7d22c82c38a`.

All decisions: [decisions.json](decisions.json), SHA-256 `00f0b0f37003ba450f25aff0bb8ed265935100beac59d8a6671ef09c5e60dbd7`; [JSONL decisions](decisions.jsonl). Exact field disagreements: [case-results.json](case-results.json). The unchanged frozen scorer returned [FALSIFIED](frozen-scorer.json).

| Control | Exact match | Action | Finding | Differing fields |
|---|---|---|---|---|
| L01 | FAIL | KEEP_FULL | FULL_BODY_SUPPORT | core_ids |
| L02 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |
| L03 | FAIL | HOLD_FOR_CITATION | CITATION_SPAN_INSUFFICIENCY | core_ids |
| L04 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L05 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L06 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L07 | FAIL | REJECT_COMPLETE | NO_SUPPORTED_CORE | citation, gap_ids |
| L08 | FAIL | REJECT_COMPLETE | CONTRADICTED_CLAIM | citation, gap_ids, witness_ids |
| L09 | PASS | WITHHOLD | INCONCLUSIVE | none |
| L10 | PASS | WITHHOLD | INCONCLUSIVE | none |
| L11 | FAIL | WITHHOLD | INCONCLUSIVE | apertures, citation, gap_ids, grounding, witness_ids |
| L12 | PASS | STOP | APPARATUS_FAILURE | none |
| L13 | PASS | STOP | APPARATUS_FAILURE | none |
| L14 | PASS | STOP | APPARATUS_FAILURE | none |
| L15 | FAIL | HOLD_FOR_CITATION | CITATION_SPAN_INSUFFICIENCY | core_ids |
| L16 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |
| L17 | FAIL | KEEP_FULL | FULL_BODY_SUPPORT | core_ids |
| L18 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |
| L19 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |
| L20 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |
| L21 | FAIL | KEEP_FULL | FULL_BODY_SUPPORT | core_ids |
| L22 | FAIL | HOLD_FOR_CITATION | CITATION_SPAN_INSUFFICIENCY | core_ids |
| L23 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L24 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L25 | FAIL | REJECT_COMPLETE | UNSAFE_DECOMPOSITION | citation, gap_ids, witness_ids |
| L26 | FAIL | WITHHOLD | INCONCLUSIVE | apertures, witness_ids |
| L27 | FAIL | REJECT_COMPLETE | CONTRADICTED_CLAIM | action, apertures, assessment_status, citation, finding, grounding, witness_ids |
| L28 | FAIL | PROPOSE_CORE_WITH_GAP | UNSUPPORTED_MATERIAL_QUALIFIER | citation |

## Paired relations

These checks compare the persisted decisions; they do not rerun the reducer. The pair file supplies prose relations. [pair-results.json](pair-results.json) records their explicit operational checks and endpoint correctness. The final column is a supplemental conjunction: relation holds and both endpoints match their frozen expectations.

| Relation | Endpoints | Relation holds | Both endpoints match / conjunction |
|---|---|---|---|
| BODY_SUPPORT_ADDITION | L02 → L15 | YES | NO |
| BODY_SUPPORT_REMOVAL | L01 → L16 | YES | NO |
| QUOTE_WIDENING | L03 → L17 | YES | NO |
| DEPENDENCY_SENSITIVITY | L02 → L04 | YES | NO |
| QUERY_INVARIANCE | L02 → L18 | YES | NO |
| HEADING_INVARIANCE | L02 → L19 | YES | NO |
| BIJECTIVE_RENAMING | L02 → L20 | YES | NO |
| WITNESS_ORDER_INVARIANCE | L01 → L21 | YES | NO |
| METADATA_INVARIANCE | L02 → L28 | YES | NO |

## Decisive failure mechanisms

Observed: six full-body-supported controls (L01, L03, L15, L17, L21, L22) return empty core_ids instead of the required retained material obligations. L03/L22 correctly distinguish body support from citation insufficiency in grounding/action, yet fail the explicit condition-retention representation.

Observed: citation differs in 16 controls; rejected decisions populate gap/witness fields where the frozen contract requires empty lists. The candidate preserves conservative rejection in these controls, but does not implement the exact contract.

Observed: L11/L26/L27 fail global uncertainty handling. L27 rejects as a contradiction and leaves N SUPPORTED; the frozen contract requires WITHHOLD and all apertures INCONCLUSIVE when authorized assessments conflict. The scorer flags L27 unsafe_support. No unsafe KEEP_FULL action or unsafe accepted core occurs, which does not rescue the failed retention and uncertainty contract.

Inference: the pre-freeze implementation assigned proposal-only meaning to core_ids and used aperture-local uncertainty/citation rules. The revealed frozen contract requires retained-ID and global-uncertainty semantics. This explains the observed discrepancies; the failed candidate remains evidence rather than being repaired after reveal.

## Source and oracle-dependency review

No forbidden dependency was detected in the frozen reducer. AST/literal review found no imports, case-ID table, historical wording, fixture/expectation file references, environment/path injection, dynamic execution, or preparation-checker dependency. Only interface enums and ordinary ledger fields appear as policy constants. The case ID is copied and validated for type/presence. Witness-order and bijective-renaming relations hold. [Source review](source-dependency-review.json), with direct runtime evidence in [decisive-run.json](decisive-run.json).

Independence achieved: qualification answers and preparation logic were excluded from the implementation context until a clean committed freeze, and the frozen reducer executes without runtime repository dependencies. Implementation and review share this qualification owner. The controls are public authored symbolic scenarios with supplied oracle-like assessments, not blind natural-language gold. This does not establish independent semantic assessment or correctness over every ledger.

## Historical consistency

A07 remains Q/N/P OVER_BROAD. Its core/decomposition safety remains NOT_ADJUDICATED; PR #22 did not establish the daily event/scope bridge, and this run makes no new core-safety judgment.

A08 remains Q OVER_BROAD and N/P SUPPORTED. Its admitted BODY says that both operations and QA signatures are a precondition to starting the run; Q omits that condition. Exact source hashes and every admitted span were verified. No historical ledger was newly authored or run, and no claim/citation was repaired. [Historical review](historical-review.json).

## Irregularities and limits

[deviations.json](deviations.json) preserves deferred coordination reads, opaque hash reconciliation, hygiene/cache failures, two pre-freeze lint attempts, the repaired apparatus collection failure, pair operationalization, and the protocol filename typo. None changed the frozen reducer after reveal, the controls, the policy, or the expected decisions. The decisive run occurred once.

The conclusion is limited to assessment_ledger → decision_record under these controls. No natural-language materiality, semantic support, decomposition safety, semantic-assessor capability, production grounding, or maintained generation behavior is qualified. Authored expectations remain agent_llm policy hypotheses, needs-audit. [Safety results](safety-results.json).

Project model/provider calls: zero. Generation/G1-G7 replays: zero. Wave B remains LOCKED. TEST/PROSPECTIVE payloads stayed closed. No CAL integration, ADR-018 change, merge, release, or branch deletion occurred.

## Disposition and next evidence

Preserve candidate 10d17b3 and close this experiment FALSIFIED. The smallest next step is a separately designed and frozen successor reducer qualification that makes retained-ID, citation, rejection-output, and global uncertainty semantics explicit. This context has now seen the controls; future qualification must account for that exposure through fresh acceptance evidence. [SUCCESSOR.md](SUCCESSOR.md) defines that boundary without implementing or running it.

Natural-language materiality/coverage assessment and safe semantic projection remain separate unresolved questions. They are not executed as a follow-up to this failed reducer.

Lineage: [issue #23](https://github.com/camerontjs-dot/biotech-rag-assistant/issues/23), [Draft PR #22](https://github.com/camerontjs-dot/biotech-rag-assistant/pull/22). Terminal machine receipt: [TERMINAL.json](TERMINAL.json); completed experiment: [EXPERIMENT.json](EXPERIMENT.json).
