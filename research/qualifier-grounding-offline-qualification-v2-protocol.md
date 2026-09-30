---
title: "Qualifier grounding offline qualification v2 preregistration"
domain: "research"
type: "experiment"
status: "designed"
source: "issue #25; frozen qualifier-grounding-policy-v2; independent fresh control author"
tags: ["ledger", "offline", "qualification", "preregistration"]
updated: "2026-09-30"
structural_type: "workflow"
lifecycle_scope: "workbench"
owner_surface: "qualifier-grounding-offline-qualification-v2"
authority: "workflow-contract"
privacy: "public-safe"
volatility: "stable"
source_of_truth: true
update_rule: "immutable after preparation freeze; changed meaning requires a successor"
---

This experiment asks whether one frozen pure reducer implements the tested v2
assessment-ledger contract without an oracle dependency. Preparation designs
and seals the contract and controls. Its execution state remains **designed /
NOT_RUN**. It establishes no semantic-assessor capability.

## Identity and evidence layers

The normative source is `qualifier-grounding-normative-v2` at commit
`ae754348d4ec8a8c6515d9dd4c67a77b07666428`, tree
`99b2c5b6ed7d084e8a73d802684f17a8904eba2c`. Its `freeze.json` binds
`policy.json`, `interface.json`, `SCHEMA.md` and `CHANGES.md` by SHA-256.
`EXPERIMENT.json` binds this protocol and the final fresh-control identity.

Predecessors are PR #24, closed FALSIFIED without merge, and PR #22, the frozen
v1 policy/apparatus. V1 publication is
`20a9f39f4368fac5b84621688aa6a334678de306`; candidate commit is
`10d17b3c56f54fca828c25c49de948051933733e`, tree
`48a1592a5f3b2e5d784115f8c834f34e879e5d2b`. Preserve them unchanged,
including failed outcomes and publication/CI failures.

The fresh acceptance set is independently authored from the frozen v2 contract
under a recorded information aperture. Its hypotheses remain agent-authored,
`evaluator=agent_llm`, `needs-audit`; they are not independently verified
natural-language truth. Schema and pair-consistency checks are preparation
evidence. Only a later valid candidate execution can produce qualification
evidence.

The original v1 inputs, expectations and pairs are **known regression
controls**. Their original hashes and roles are recorded in `regression.json`.
They remain under their original interface/expectations; do not rewrite them
as v2 answers. V2 adds diagnostics and explicitly changes some citation and
guard semantics. Therefore original v1 exact labels are a historical
compatibility measurement, never native v2 acceptance keys.

## Normative authority

The v2 policy, interface and encoding guide are frozen before any fresh control
author reads them. If the contract lacks a necessary rule, stop this experiment
with INCONCLUSIVE or APPARATUS_INVALID and design a separately identified
successor. Do not infer a missing rule from expectations and change the
normative package after reveal.

> **Binds:** control authors, reducer implementers and qualification owners for v2
> **Tier:** T0 (preparation custody is checked; future execution enforcement is NOT_RUN)
> **Check:** preparation checker verifies hash bindings and chronology; later owner reviews contract/source/reveal evidence
> **Escape:** preserve the defect and stop; freeze a new identity for changed meanings

## Implementation aperture and candidate freeze

A separately authorized implementer must start without exposure to either fresh
acceptance answers/cases or known predecessor controls, answers, reducer, case
results, historical anchors or qualification traces. It may read only issue
#25's objective/boundaries with per-case evidence removed, the v2 policy,
interface, a minimal candidate identity/state manifest, and ordinary engineering
conventions. Do not expose SCHEMA.md's acceptance artifacts, CHANGES.md's known
outcomes, this full protocol, preparation checker/tests or experiment answer
bindings as implementation aids. Supply a filtered implementation packet from
the frozen package; preserve its actual contents and hashes. A clean Git
checkout alone is insufficient because this branch contains public answers.

The implementer creates the smallest deterministic pure `decide` entrypoint
from ledger structure and declared assessments. It must not consult models,
external services, hidden prose, case IDs, repository history, fixture files,
expected decisions, environment variables or paths as answer sources. It must
not manufacture semantic judgments or elevate QUERY/HEADING/METADATA into
BODY support. Implementation-local tests derive from the policy/interface,
with no reconstruction of qualification cases.

Before reveal, complete source and ordinary local checks, inspect imports and
runtime file/network/process/environment access, commit source, record exact
branch/commit/tree and file hashes, environment and contamination status, and
verify a clean checkout. Create a candidate freeze receipt outside the source
commit or in a later identity-only receipt commit; keep the implementation tree
and hashes explicit. No implementation is supplied or run in this preparation.

> **Binds:** separately authorized v2 implementer and qualification owner
> **Tier:** T0 (execution not yet authorized or implemented)
> **Check:** future candidate freeze, local checks and source/dependency inspection
> **Escape:** contaminated aperture stops with CONTAMINATED; missing source/environment stops without a run

## Reveal and single decisive run

After the clean candidate freeze, record the first reveal time and newly
accessible inputs, expectations, pairs and apparatus by exact identity. Keep
all implementation source bytes frozen. Run the frozen candidate exactly once
per fresh input in a single decisive run; persist every decision-only output
before scoring against the expectation file. No scorer or expectation import
may influence the reducer's runtime.

Then evaluate each frozen pair against the persisted endpoint decisions.
INVARIANT compares the listed fields; RENAMED_INVARIANT maps identifier
namespaces and canonicalizes renamed arrays; SENSITIVITY requires every
listed equal/different field relation. Pairs are not extra reducer calls. Both
endpoints must also match their exact expectations; relation-only passes are
reported separately and cannot compensate for a failed endpoint.

An exclusive run-start receipt prevents repeated runs under the same candidate.
Missing candidate, input drift, malformed outputs or an interrupted/partial run
produce APPARATUS_INVALID with actual outputs and failures preserved. Do not
quietly retry and count a later attempt as the same decisive run. An
independently declared execution-environment successor may be designed later.

> **Binds:** future v2 qualification owner and apparatus
> **Tier:** T0 (single-run enforcement must be implemented and reviewed in the execution task)
> **Check:** future exclusive run-start receipt, call counts, output custody and timestamps
> **Escape:** preserve partial execution; stop without repair or a substituted run

## Separate regression reporting

Only after candidate freeze, the same unchanged candidate may be run once over
the original known regression inputs as a separately identified regression
phase. This phase is optional compatibility evidence, not the decisive fresh
acceptance run. If omitted, report regression NOT_RUN; it never substitutes for
fresh acceptance.

If run, report each original input's v2 decision, compare the overlapping v1
fields against the unchanged v1 expectation (excluding reason), and report
original pair relations separately. Added v2 diagnostics are retained but are
not fabricated into v1 expectations. Label exact legacy matches and legacy
disagreements as such. Do not score them as v2 exact correctness or invent an
average spanning versions. Enumerate which discrepancies follow the frozen v2
semantic changes and which remain unexplained. A revealed safety violation of
the v2 policy falsifies the candidate even if it occurs on a known input; mere
disagreement with an explicitly changed v1 label is not such a violation.

> **Binds:** future regression owner and report author
> **Tier:** T0 (legacy bytes are checked now; future compatibility scoring is NOT_RUN)
> **Check:** unchanged regression hashes and separately named per-case/pair reports
> **Escape:** omit regression as NOT_RUN rather than present incompatible labels as acceptance keys

## Exact acceptance and falsification

A valid run receives SUPPORTED_FOR_LEDGER_CONTRACT only if every fresh decision
has the exact required schema and canonical identifier lists and matches every
frozen expected field except the content of `reason`; every fresh paired
relation holds with two exact endpoints; and source/runtime review detects no
oracle dependency. The explanation must be nonempty and may not contain answer
prose or introduce unauthorized output fields. There is no average-score
acceptance threshold.

Any validly observed fresh-case mismatch, failed relation, unsupported full
claim/core authorization, lost supported condition, unknown-to-support
conversion, unauthorized support, citation/packet conflation, contradiction
hidden by trimming, unsafe accepted decomposition, apparatus failure treated
as semantics, or diagnostic IDs treated as retained output yields FALSIFIED.
Required global uncertainty forbids locally SUPPORTED authority outside the
diagnostic channel. Safety failure in any observed input cannot be masked by
fresh or regression averages or pair relation successes.

Distinguish dispositions:

- `SUPPORTED_FOR_LEDGER_CONTRACT`: every strict fresh gate passes, no v2 safety
  violation observed, no prohibited dependency detected, valid execution.
- `FALSIFIED`: valid execution yields any contractual failure or detected
  implementation shortcut/oracle dependency after a valid clean freeze.
- `CONTAMINATED`: the implementation/control-author information aperture
  includes forbidden qualification evidence before its respective freeze.
  Preserve exposure evidence; no independence claim.
- `APPARATUS_INVALID`: missing/drifted artifacts, invalid integrity/custody of
  the qualification apparatus itself, malformed submission or incomplete run
  prevents valid scoring. An input that deliberately declares an integrity
  failure is a valid control expecting STOP; it does not itself invalidate the
  qualification apparatus.
- `INCONCLUSIVE`: a material ambiguity in authority or evidence prevents a
  bounded decision; preserve the uncertainty rather than alter frozen rules.

Report direct outputs, source-access events, schema failures and comparisons
separately from qualitative interpretation. A passing result establishes only:
“This frozen reducer correctly implements the tested frozen assessment-ledger
policy contract under these controls.”

> **Binds:** qualification owner, scorer and terminal receipt author
> **Tier:** T0 (preparation defines the gates; no v2 execution/scorer exists yet)
> **Check:** future exact per-case/pair reports, source review and terminal receipt
> **Escape:** retain every mismatch and stop; never fix until green inside this qualification

## Source/oracle review and no repair

Review the frozen reducer after the decisive run. Use AST/static inspection,
isolated runtime instrumentation and exact source hashes where practical. Check
case-ID branches/tables, copied answer records, fixtures/expectations, history
or historical anchor text, hidden preparation-checker/scorer imports,
environment/path answer injection, dynamic execution, network/process/file
access, identifier/order dependence, and output copied from a scorer instead
of derived from policy state. Enum constants are necessary interface literals;
case-keyed answer objects are prohibited. Document the independence achieved
and limitations rather than equating another process with independence.

If material repair is needed after reveal, terminate v2 and design a new
candidate/experiment. Preserve the failing candidate, outputs, diagnostics,
deviations and original expectations. Never modify v1 or v2 frozen artifacts
to obtain a preferred result.

> **Binds:** future implementation/qualification owner
> **Tier:** T0 (review methods preregistered, NOT_RUN)
> **Check:** future source/oracle receipt, runtime trace, candidate hash comparison
> **Escape:** FALSIFIED/CONTAMINATED/APPARATUS_INVALID as applicable; separate successor for repair

## Protected boundary and next task

Zero project model/provider calls. No generated claims, generation or G1-G7
replay, old-output repair, prompt tuning, Wave B/TEST/PROSPECTIVE payloads, CAL
integration, ADR-018 modification, v1 reducer repair/rerun, v2 implementation or
decisive execution during preparation, maintained-generation promotion, merge
or release. **Wave B remains LOCKED.**

> **Binds:** preparation and later bounded reducer-qualification owners
> **Tier:** T0 (explicit scope, source diff and receipts; no production enforcement claimed)
> **Check:** changed-file inventory and zero project-call/execution receipts
> **Escape:** stop for a new semantic experiment or protected operation outside authorization

The smallest next evidence-producing step is a separately authorized v2
implementation/qualification owner starting from a clean implementation
aperture, freezing one pure reducer, then performing the preregistered reveal
and single decisive run. Natural-language materiality, support and safety
assessment remain a separate unresolved semantic-assessor question. Do not
execute either step here.
