---
title: "Ledger policy v2 semantic changes"
domain: "research"
type: "decision-record"
status: "frozen"
source: "issue #25; frozen v1 policy/interface; v1 implementation rationale and terminal evidence"
tags: ["ledger", "policy", "design"]
updated: "2026-09-30"
---

The v1 reducer is FALSIFIED. Its complete evidence remains unchanged. This is a
new normative identity, `qualifier-grounding-policy-v2`, with interface
`qualifier-grounding-interface-v2` and package `qualifier-grounding-normative-v2`.
It changes allowed records and adds diagnostics, so it cannot be called a v1
clarification with the same identity.

| Ambiguity exposed by v1 | Explicit v2 meaning |
| --- | --- |
| Complete support versus projection-only `core_ids` | KEEP_FULL and HOLD_FOR_CITATION retain every material obligation ID. PROPOSE_CORE_WITH_GAP retains exactly the supported subset. |
| Missing content and witnesses on rejected decisions | REJECT_COMPLETE, WITHHOLD and STOP clear all authoritative ID lists. Diagnostic missing content and assessed witnesses live in a separately labelled object; STOP clears that object except its apparatus code. |
| Quote versus nomination insufficiency | Citation is decided from Q/N only: deficient N precedes deficient Q. With full N and deficient Q use QUOTE_INSUFFICIENT; with deficient N use NOMINATION_INSUFFICIENT even when P is full. P defects do not directly pick a citation enum. This expressly differs from the v1 answer key's quote-insufficient labels on some incomplete nominations. |
| Uncertainty propagation | Unknown coverage/materiality, authorized ambiguity/conflict and applicable unknown guards collapse all authoritative apertures, grounding and citation to INCONCLUSIVE. Locally supported diagnostics carry no retention authority. |
| Contradiction versus conflicting assessments | Pure packet contradiction rejects; same-aperture entailment plus contradiction is global uncertainty. Silence and complementary partial witnesses are not conflicts. |
| Guard applicability and precedence | Guards apply only to partial supported packet content with no earlier uncertainty/contradiction. Any applicable null guard precedes false guards. Proposals cannot manufacture a safe core or trim a fully supported condition. |
| Integrity uncertainty | New `integrity: UNKNOWN` yields apparatus STOP, rather than a semantic withhold. Schema/referential errors also stop. |
| Arbitrary witness selection/order | Full-content retention uses every contributing authorized packet BODY witness. Projection uses exactly the declared accepted witnesses. Input order and identifier spelling cannot change behavior. |

Unchanged boundaries: assessments are declared; Q uses QUOTE and N/P use BODY;
QUERY/HEADING/METADATA are never support; complete material coverage is required;
all six safety guards remain; original complete claims stay non-supported when
only a safe core is proposed; quote omissions do not erase body-supported
conditions; contradiction cannot be hidden by trimming; no answer prose or
semantic assessor is implemented. ADR-018 and maintained generation behavior
are untouched. Wave B remains LOCKED.

Direct observations from the v1 terminal receipt: 28 calls, five exact matches,
23 disagreements, nine relation successes with zero pairs having two exact
endpoints; six full-content retention failures, 16 citation disagreements, and
global uncertainty failures. Source/runtime review found no forbidden oracle
dependency. Inference: these justify explicit contract design, but do not prove
that every new normative choice is optimal or that a v2 reducer will pass.

The known v1 controls remain regression evidence under their original v1
expectations. They cannot be exact v2 acceptance keys because this interface
adds required diagnostics and explicitly changes some semantics. A future run
may publish v2 records on those same unchanged inputs with an explicitly
versioned compatibility analysis; it must not silently reinterpret the old
expectations or count their success as fresh qualification. Fresh controls are
authored only after this normative freeze by a context that excludes v1 cases,
answers, reducer and history.

Non-claims: no arbitrary-prose materiality, semantic support, safe decomposition,
production grounding, semantic assessor reliability, universal ledger
correctness, reducer execution, model/provider calls, promotion, merge or
release. The policy is agent-authored design, `evaluator=agent_llm`, `needs-audit`.

Structural profile: public workbench decision record owned by the v2 normative
package; immutable after freeze; authority is this bounded design; verification
is hash/custody and structural review, not scientific outcome qualification.
