---
title: "Frozen v2 ledger reducer qualification execution"
domain: "research"
type: "experiment"
status: "terminal"
source: "issue #27; PR #26 frozen preparation; persisted execution receipts"
tags: ["ledger", "offline", "qualification", "reducer"]
updated: "2026-09-30"
structural_type: "project-entry"
lifecycle_scope: "workbench"
owner_surface: "qualifier-grounding-offline-qualification-v2 execution"
authority: "project-status"
privacy: "public-safe"
volatility: "stable"
source_of_truth: false
update_rule: "append publication observations; preserve frozen source and raw outputs"
---

The terminal disposition is **SUPPORTED_FOR_LEDGER_CONTRACT**. One frozen pure
reducer matches every required field on all 69 fresh controls and all 33 frozen
relations with exact endpoints. Every fresh ledger was called once; decisions
were persisted before scoring. Pair scoring made zero reducer calls.

The candidate is `1ff76f74dc15e997923d7002e48d8e56cdb11d30`, tree
`617fe8fae6b5cb9ed466ec86567c43260473f4b0`. Its freeze preceded reveal at
`2026-10-01T03:36:46.870144+00:00`. The exact pre-freeze aperture is recorded in
[implementation-aperture.json](implementation-aperture.json); source/environment
identity is in [candidate-freeze.json](candidate-freeze.json). No forbidden
pre-freeze qualification content exposure was observed.

The [fresh decisions](fresh-decisions.jsonl), [call journal](fresh-call-journal.jsonl),
[case comparisons](fresh-case-results.json) and [pair results](fresh-pair-results.json)
are the primary output evidence. The [source/oracle review](source-oracle-review.json)
finds no prohibited dependency or runtime access event and no declared v2 safety
violation across the 97 observed fresh/regression inputs. This is restricted
information/runtime separation; it is not independent human review or proof of
all possible ledgers.

The separately reported [legacy regression](regression-scoring.json) has 14 exact
legacy matches and 14 citation-only disagreements. All nine legacy relations hold,
but only two have exact legacy endpoints. The [interpretation](regression-interpretation.json)
checks that all disagreements follow frozen v2 nomination-before-quote precedence.
Original v1 expectations are preserved and are not native v2 acceptance truth.

Candidate-local tests and correctness lint passed before freeze. Repository-style
lint reports seven findings in frozen candidate/tests and 23 in execution tools,
separate from the 265 inherited frozen author-helper findings. These records are
preserved; no green repository/publication claim is made and no frozen source is
repaired. Local apparatus-copy and instrumentation setup failures occurred before
the decisive run and are preserved in [deviations](deviations.json).

The preparation records remain unchanged. [TERMINAL.json](TERMINAL.json) and
[EXPERIMENT.json](EXPERIMENT.json) record this execution without replacing them.
The preserved scorer can recompute comparisons from these persisted outputs;
it imports no candidate and makes no reducer calls. Do not rerun this candidate
as another attempt of the same experiment.

Natural-language materiality, BODY support, coverage and decomposition-guard
assessment remain unestablished. The next evidence step requires a separately
authorized, preregistered control with independent natural-language adjudication.
No semantic-assessor experiment ran here. Zero project model/provider calls;
Wave B remains LOCKED. No generation, protected payload access, CAL integration,
ADR-018 change, promotion, merge or release.
