---
title: "Material qualifier grounding policy and offline qualification preregistration"
domain: "ai-systems"
type: "protocol"
status: "preregistered"
source: "Issue 21; frozen PR 20; accepted ADR-018"
tags: ["grounding", "qualifiers", "offline", "preregistration"]
updated: "2026-09-30"
structural_type: "workflow"
lifecycle_scope: "workbench"
owner_surface: "research/evidence/qualifier-grounding-policy-v1"
authority: "workflow-contract"
privacy: "public-safe"
volatility: "stable"
source_of_truth: true
update_rule: "new-successor-on-material-change"
verification: ["research/check_qualifier_grounding_preregistration.py", "tests/test_qualifier_grounding_preregistration.py"]
do_not_use_for: ["semantic capability claims", "public generation", "Wave B execution"]
---

# Material qualifier grounding preparation

Package ID: `qualifier-grounding-policy-v1`.
Next qualification ID: `qualifier-grounding-offline-qualification-v1` (designed,
NOT_RUN). This package freezes a policy, an assessment interface, controls and a
mechanical contract checker. It does not implement a semantic assessor or change
the production generation boundary.

## Question and fixed authority

How should the boundary handle a material proposition missing from authorized
evidence while retaining conditions that the admitted body actually supports?

Source: PR #20 head `bdcc8f0a315e7454dffb878b87f8ad51a9a25fd9`, tree
`cfdb88587d317fadd2fd22f097d16c0c7fa07619`. Predecessor adjudication SHA-256
`6610b9a21ce7cc33cea39a197d4c689f8eacc6035be88caf6ecf6c502b8b6f21`;
freeze `ff7ba96166485e1af74a6896d9463bdbc83049f209d74eaf38e8577548403e61`;
protocol `97120d8e6e1fc09036be92a096ec2c0c0d6ef99fd5cd35c345097147db3036b4`.

PR #17 remains historically `APERTURE_AUTHORITY_UNDEFINED`; PR #19's ADR-018
and PR #20's `MIXED` remain unchanged. `custody.json` pins the eleven preserved
first-run files, twelve successor records, exact authority sources, and six
admitted A07/A08 body spans. Only these two cases provide observed semantic
evidence. Existing structural gate code is inspected, not replayed.

Under ADR-018, Q is the selected quote, N the cited body, and P all admitted
body spans. Source hashes and character spans establish custody in this frozen
package. An ep1 ID alone does not authenticate body text. The question identifies
the requested fact; headings, query text, titles, rankings and other metadata
cannot supply a missing semantic proposition. No unadmitted source context is
added to P. Narrow G5 identifier membership does not confer semantic authority.

## General policy and challenge

A full claim is grounded only if authorized evidence supports every material
proposition asserted or presupposed by that claim, including the relations that
attach qualifiers to the correct actor, object and event. Support is entailment
of meaning, not word overlap or independent presence of all its nouns. A
conditional obligation is not an assertion that the action already happened.
Materiality applies to the claim text and any qualifier or limitation fields.

If a separately supported core can be presented without carrying the missing
proposition or changing its meaning, the proposed action is to retain that
bounded source core with an explicit grounding gap. The original full claim
remains `OVER_BROAD` or `UNSUPPORTED`; it never becomes `SUPPORTED` because a
smaller statement is available. The core proposal is a new, attributed projection
with a link to the unchanged original, not an edit to the original output.
No projection is emitted in this preparation or its offline qualification.

The candidate rule needs a safety restriction: deleting text is not evidence of
safe decomposition. A source-supported conditional, exception, restriction,
negation, obligation, quantifier, event binding or other material content must
remain attached to the core when needed to preserve its meaning. Removing an
antecedent can create an unconditional obligation; removing a negation can invert
a fact; removing a population restriction can broaden a requirement. Those
projections fail closed. A relevant quote with fewer words is not automatically
an acceptable smaller claim.

If P supplies the full meaning while Q omits a condition, record citation-span
insufficiency separately. Retain the supported condition in the support judgment;
hold the proposed complete claim for a sufficient citation witness. Do not label
it a packet grounding defect or strip a supported condition to fit the quote.
Nothing here repairs an old citation or bypasses existing G1-G7 checks.

## Operational materiality and decomposition

The smallest representation is an **assessment ledger**, not a universal semantic
ontology. It has obligation IDs, per-aperture support assessments with exact
witnesses, a coverage declaration, and a proposed core/gap partition with six
safety guards. Obligations can bundle a relation whose meaning cannot be split.

A qualifier is material when changing or removing it can change at least one of:
truth conditions, referent/event identity, actor/object binding, population or
temporal scope, quantity/degree, polarity, obligation/permission, precondition,
exception, or required action. The assessor records the counterfactual change
that makes it material. Purely stylistic wording may be non-material only with a
meaning-preservation rationale. Uncertain materiality is `INCONCLUSIVE`.

Safe decomposition requires **all** of the following, each with a rationale:

1. Coverage accounts for all material content of the original claim. Unenumerated
   content cannot disappear merely because the retained core looks plausible.
2. The retained core is independently entailed by admitted body evidence, with an
   exact source witness. It contains the body's necessary conditions and limits.
3. Actor, object, event, polarity, modality and quantity bindings stay intact.
4. Removing a qualifier does not remove an antecedent, exception, domain guard or
   other dependency that changes the retained proposition's meaning.
5. The core has meaning without presupposing the missing qualifier. It is presented
   as a bounded source fact, not as a complete answer to the qualified question.
6. The gap names the removed material proposition and accompanies the core. The
   full original claim remains non-supported. No unknown qualifier is asserted
   false merely because it is absent from this packet.

A guard established false => `UNSAFE_DECOMPOSITION`, reject the complete claim.
A guard not reliably established => `INCONCLUSIVE`, withhold the claim/projection.
P support missing entirely or contradicted => reject; no core is manufactured.

> **Binds:** proposed ep1 qualifier-grounding decisions in this offline research line.
> **Tier:** T0 (semantic assessments and projection safety require review).
> **Check:** a complete ledger, exact evidence witnesses, explicit safety rationales, and the frozen control expectations.
> **Escape:** `INCONCLUSIVE` or rejection; no automatic rewrite, unauthorized evidence import or favorable aperture selection.

## Interface and assessment authority

The qualification candidate is a pure offline function:

`decide(assessment_ledger) -> decision_record`

`interface.json` freezes required fields and enums. `inputs.json` contains authored
ledger controls; `expectations.json` is a separate oracle withheld from the
candidate's input. The contract checker can compare a later submission, but no
candidate is implemented or qualified in this package.

An upstream semantic assessor must map an exact natural-language claim and
authorized body to this ledger. That assessor is **not implemented** here.
Model-owned decomposition, unsupported lexical matching, and query/heading text
cannot become trusted assessments without qualification. Supplied assessments
are explicit oracle-like inputs, not independent semantic findings. A decision
reducer passing them establishes conditional policy behavior only.

For historical A07/A08, the raw claim/citation/question/P surfaces are pinned
unchanged in `historical.json`. Existing Q/N/P labels are inherited observations
of agent judgment (`needs-audit`), not fresh deterministic labels. A07 core safety
is deliberately **not** adjudicated here: the daily event/scope bridge needs
review before a source-core projection can be proposed. A07's full P claim must
stay non-supported under the accepted rule. A08 must retain its body-supported
pre-run obligation while reporting Q's omission.

The next qualification tests the reducer on declared ledgers and separately
records historical safety-review disagreement. It cannot claim to discover
qualifiers in arbitrary prose. A later semantic assessor needs its own frozen
qualification; if stronger machinery or a changed aperture is necessary, stop
and identify that successor rather than broadening this one.

## Preregistered controls and expectations

Controls are **authored symbolic ledger scenarios**, not provider outputs, repaired
claims, new factual source documents, or new ep1 packets. Their vocabulary is
opaque. Structures are motivated by the frozen scope/condition failures and
general dependency counterexamples. Text is never manufactured as model output.
All material expectations are policy hypotheses, `evaluator: agent_llm`,
`needs-audit`; a disagreeing review remains evidence against the design.

The fixed suite includes full body support, unsupported material scope,
quote-only omission with full body support, unsafe antecedent/negation/domain
removal, complete lack of core support, contradictory evidence, ambiguous
materiality/coverage/binding, and apparatus disconnection/custody failure.
Paired controls test body-support removal/addition, qualifier dependency changes,
query/heading changes, opaque-ID renaming, quote widening, witness order, and
conditions present in a different admitted body. No literal keyword controls
such as checking for `daily` are permitted in a candidate implementation.

Positive controls require complete support or a safely bounded core plus gap.
Always-reject and always-`INCONCLUSIVE` implementations therefore cannot pass.
Negative controls require the full claim to remain non-supported. Always-support,
query-as-evidence, quote-equals-packet, blind qualifier deletion, and bag-of-words
support implementations have named failure opportunities in `expectations.json`.
The mechanical scorer checks required outcomes, core/gap partitions and witness
references; it does not establish the semantic correctness of the input ledger.
Finite public controls cannot defeat a lookup table alone: the next qualification
also records candidate source and verifies it cannot read expectations/fixtures
by case ID, use keyword exceptions, or import historical verdicts as computation.

## Qualification outcomes and stopping rules

- **SUPPORT_FOR_LEDGER_POLICY_ONLY:** every fixed control and required pair relation
  passes, no scope/custody/schema failures, no forbidden oracle dependency, and
  implementation review finds no case/word lookup. This supports the reducer for
  the declared ledger boundary; it does not solve semantic grounding.
- **FALSIFIED:** any valid control receives an incorrectly permissive full-claim
  judgment, loses a supported condition, emits an unsafe core, conceals a gap, or
  changes under an irrelevant context mutation. Preserve the first candidate,
  traces and failing controls. A corrected candidate gets a new identity.
- **MATERIALLY_WEAKENED:** no unsafe acceptance, but determinate positive controls
  are rejected/abstained, or safe decomposition cannot retain the expected core.
- **INCONCLUSIVE:** ledger materiality, coverage, binding or historical safety is
  not reliably established. Withhold the claim. Do not count abstention as pass
  on controls whose expectations are determinate. If the ambiguity makes the
  policy distinction untestable, terminate the qualification as inconclusive.
- **APPARATUS_FAILURE:** missing/altered input, broken custody, absent candidate,
  malformed/missing/duplicate result, dependency error or execution exception.
  Stop the affected qualification; no semantic conclusion or fake success.

All controls are required. No averaged score masks an unsafe acceptance. A07/A08
remain historical anchors; neither their known labels nor a successful schema
check qualifies a semantic detector. Historical A07 projection safety can remain
inconclusive even if the declared-ledger reducer passes its controls.

The smallest next evidence-producing step is separately pinning one pure offline
ledger reducer, then running this fixed contract once and reviewing its source
and exact historical ledger/safety evidence. Record decision-only traces; emit
no answer text. No new model, provider response, G1-G7 replay, prompt, repaired
claim, expanded aperture or protected data is required or authorized.

## Freeze and protected boundary

`freeze.json` pins this protocol, policy, interface, controls, expectations,
historical bindings, custody receipt, checker and tests. Material design/input/
expectation changes after publication require a new package/qualification ID.
Preparation checks and diagnostics remain separate from qualification outcomes.

> **Binds:** this preparation and its designed offline qualification.
> **Tier:** T1 for declared hashes/schema/bindings; T0 for operator scope and semantic authority.
> **Check:** `python research/check_qualifier_grounding_preregistration.py --out preparation-check.json`; `python -m pytest tests/test_qualifier_grounding_preregistration.py`; explicit Git/source receipts.
> **Escape:** preserve failed/degraded preparation, `APPARATUS_FAILURE`, or `INCONCLUSIVE`; never reconstruct missing outputs or expand authority.

Wave B is **LOCKED**. No model/provider generation path, new generated output,
frozen-output replay/repair, prompt tuning, Wave B payload access, TEST or
PROSPECTIVE material, CAL integration, ADR-018 change, public generation promotion,
merge or release is authorized. The next qualification remains NOT_RUN until its
candidate and execution are separately authorized.
