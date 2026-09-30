---
title: "Qualifier grounding preparation receipt"
domain: "ai-systems"
type: "research-receipt"
status: "synthesized"
source: "Frozen PR 20, issue 21, native contract checks"
tags: ["grounding", "qualifiers", "offline", "needs-audit"]
updated: "2026-09-30"
---

# Frozen qualifier grounding preparation

Terminal state: **TERMINAL — preparation package frozen**.
Package: `qualifier-grounding-policy-v1`.
Branch: `codex/material-qualifier-grounding-v1`.
The semantic grounding problem remains unqualified. No semantic assessor or
policy candidate has run; `qualifier-grounding-offline-qualification-v1` is
designed and **NOT_RUN**.

## Policy and representation

The full claim needs support for every material assertion, presupposition and
attachment relation. A missing qualifier cannot become supported through the
query, heading or metadata. A safe source-core proposal needs independent body
support, preserved bindings and conditions, an independent removal, no missing
presupposition, and an explicit accompanying gap. False safety guards reject;
unknown guards withhold. The original claim stays unchanged and non-supported.

The candidate rule was refined to prevent deletion from broadening a conditional
or restricted proposition. Citation sufficiency is separate: body-supported
conditions survive the support judgment even when the selected quote omits them;
the complete claim is held for a sufficient citation witness. No citation or
claim is repaired in this package.

The small representation is a material-obligation assessment ledger, exact
per-aperture witnesses, coverage/integrity state and six projection-safety guards.
[Protocol](../../qualifier-grounding-policy-v1-protocol.md), [policy](policy.json),
[interface](interface.json), [inputs](inputs.jsonl),
[expectations](expectations.jsonl), and [paired controls](pairs.json) are frozen.
The pure candidate interface is `decide(assessment_ledger) -> decision_record`.
The checker validates declared assessments and scores a later submission; it
does not infer entailment from prose or authenticate an assessor by its labels.

## Declared controls

| Category | Count | Required distinction |
| --- | ---: | --- |
| Positive | 1 | Full body/quote support keeps the complete meaning. |
| Negative | 3 | Query/heading-only scope, absent core, and contradiction cannot pass. |
| Citation | 2 | Quote/cited-body omission differs from a full-packet defect. |
| Unsafe decomposition | 6 | Antecedent, polarity, domain/event binding, gap visibility and supported conditions constrain projection. |
| Ambiguous | 5 | Materiality, coverage, binding, body ambiguity and conflict can remain inconclusive. |
| Apparatus | 3 | Custody failure, absent assessor and execution failure stop adjudication. |
| Sensitivity | 3 | Body support addition/removal and quote widening must change the proper result. |
| Invariance | 5 | Query, heading, metadata, opaque ID and witness-order changes preserve meaning. |

There are 28 authored ledger controls and nine paired relations. These are
explicit oracle-like assessment inputs, not new generated claims or provider
responses. Their expectations are agent-authored policy hypotheses,
`needs-audit`. Passing them can establish conditional reducer behavior only.
Always-support, blanket qualifier deletion, quote/packet conflation, favorable
witness selection, always-reject and always-inconclusive policies have failure
opportunities. The public finite suite alone cannot exclude a lookup table;
candidate source/oracle-dependency review is mandatory in qualification.

## Unchanged historical anchors

Only A07/A08 provide observed semantic evidence. [historical.json](historical.json)
binds exact claims, citations, questions and prior public results to the preserved
PR #20 surfaces. The inherited judgments are agent judgments, not fresh labels.

- A07 remains Q/N/P `OVER_BROAD`, packet-level grounding defect. The two-weight
  before-use body does not supply daily-check scope under ADR-018. A source-core
  proposal requires a separate event/scope and safety review; its safety is
  **not adjudicated here**. Query versus excluded-heading causal origin remains
  undetermined. No smaller answer text was created.
- A08 remains Q `OVER_BROAD`, N/P `SUPPORTED`, citation-span insufficiency. The
  required pre-run signing condition is present in the cited body and must not
  be stripped merely to fit the short quote. No citation repair occurred.

PR #17's historical `APERTURE_AUTHORITY_UNDEFINED`, PR #19's accepted ADR-018,
and PR #20's `MIXED` are unchanged. Native source observation: G1-G7 enforce named
structural checks; neither the optional qualifier field nor a valid gap citation
establishs complete semantic coverage or safe decomposition. A07's qualifier
field was null despite its material scope wording in the claim text.

## Exact frozen authority

Source head: `bdcc8f0a315e7454dffb878b87f8ad51a9a25fd9`.
Source tree: `cfdb88587d317fadd2fd22f097d16c0c7fa07619`.
The GitHub PR/issue terminal receipt records this package's own commit/tree;
a manifest cannot contain its own commit SHA.

```text
predecessor adjudication 6610b9a21ce7cc33cea39a197d4c689f8eacc6035be88caf6ecf6c502b8b6f21
predecessor freeze       ff7ba96166485e1af74a6896d9463bdbc83049f209d74eaf38e8577548403e61
predecessor protocol     97120d8e6e1fc09036be92a096ec2c0c0d6ef99fd5cd35c345097147db3036b4
this protocol            85ba07c4183dd2413d7c796f9a4f164f692012f93367c49fbda75378c867b8dc
policy                   40691a83cdc901df9f2af903bc7a48a936e6602a622926460286bb25eeec869f
interface                70759527cea4aaf8213edcfdb3fc191486cc4bf53ee9a8196ca10fd51b87d489
inputs                   8667dd6fa1718f16c9a0ba445380f15c9c31befffee18a72b2c1f843d132228f
expectations             28c17fa63641a227710fa74b12dda6b9a51b4c3ce56d805ec447579197c74f47
preparation freeze       b327af7fc2db7bec3ef1f868027c88d30a2c7f7778fde55765c249c18d1f898d
```

[freeze.json](freeze.json) pins twelve normative files.
[custody.json](custody.json) checks 37 authority/evidence files, including all
eleven originally preserved files, twelve successor records and six body spans.
[receipt-freeze.json](receipt-freeze.json) pins preparation traces and diagnostics.
No omitted historical artifacts were reconstructed; PR #17's selective
preservation limits still apply.

## Preparation observations and deviations

[Preparation checker receipt](preparation-check.json):
`PASS_PREREGISTRATION_CONTRACT_ONLY`, 28 controls, nine pairs, two historical
bindings, qualification NOT_RUN. Sixteen native pytest contract selftests passed
with Python 3.11.15; Ruff 0.15.16 and contract lint passed. The scorer's oracle and
adversarial probes test the grading contract, not a candidate's semantic ability.
[Check receipts](checks.json) retain stdout/stderr, exits and hashes.

A falsifier exposed the first checker's one-direction support check: fully
witnessed body coverage could be mislabeled unsupported. The adversarial test
failed; its checker, preliminary freeze and trace are preserved. The correction
checks all declared aperture classes in both directions. The policy, controls,
expectations, guards and historical evidence did not change. Initial sparse setup
also reported missing unrelated workflow blobs; the exact final checkout and all
allowed evidence were verified before design. The first commit failed before
creating an object because the shared clone lacked a workflow blob/promisor
configuration. The exact workflow Git blob was restored with its SHA-1 verified;
only the isolated object store/configuration changed. No protected payload was
fetched or materialized. [Deviations](deviations.json).

Only checkout prefixes in public diagnostic logs were sanitized. Exact local
logs were retained. No model/provider bytes were transformed. The ordinary dirty
workbench and predecessor checkouts were preserved; no source integration or
generation code changed.

## Next evidence-producing step

Separately authorize and pin one pure offline ledger reducer for the designed
`qualifier-grounding-offline-qualification-v1`. Run the fixed controls once,
preserve per-control decision-only traces, and review the candidate for oracle/
case/keyword dependencies. Review A07's core event binding and safety separately;
preserve disagreement or inconclusive review. This can qualify a ledger policy,
not an arbitrary-prose semantic assessor. That assessor remains the next unknown.

**Wave B: LOCKED.** Zero project model/provider calls, fresh generated outputs,
generation/gate replays, prompt changes or output repairs. No Wave B payload,
TEST/PROSPECTIVE material, CAL integration, ADR-018 change, public-generation
promotion, merge or release. The qualification successor has not executed.
