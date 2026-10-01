---
title: "Semantic assessment annotation rubric v1"
domain: "ai-systems"
type: "workflow"
status: "preregistered"
updated: "2026-10-01"
source: "issue #29; independently specified annotation contract"
tags: ["semantic-assessment", "annotation", "research-preparation"]
structural_type: "workflow"
lifecycle_scope: "workbench"
owner_surface: "qualifier-grounding-semantic-assessor-controls-v1"
authority: "workflow-contract"
privacy: "public-safe"
volatility: "stable"
source_of_truth: true
update_rule: "immutable after rubric freeze; changed meaning requires a successor"
---

# Semantic assessment annotation rubric v1

**Trigger:** a separately authorized annotation or assessor implementation using this rubric.
**Stop state:** a preserved annotation, including justified UNKNOWN values, or an explicit
contamination/invalidity receipt. This preparation does not authorize annotation execution.
**Owner surface:** `qualifier-grounding-semantic-assessor-controls-v1`.

This is a proposed operational definition for a finite, synthetic English control set.
It has not been validated by adjudicators. It does not establish real-world truth.
The annotation concerns claim meaning relative to the admitted BODY text. Source
admission, document currency, retrieval, citation selection, and answer generation are
outside this arrow. The qualified ledger reducer cannot supply semantic judgments.

## 1. Represent every material assertion and constraint with its scope intact.

> **Binds:** case annotators, reconcilers, and future semantic assessors
> **Tier:** T0
> **Check:** none for semantic completeness; future independent annotation assurance is preregistered
> **Escape:** represent the uncertain item as UNKNOWN and set coverage UNKNOWN; do not invent a reading

A material obligation is an assertion, presupposition, restriction, condition, binding,
or relation whose deletion or change can change the claim's truth conditions or what
actor must/may do what to which object, in which event, time, domain, amount, or degree.
Materiality is semantic dependence, not keyword salience or document importance.

Use this procedure, before judging BODY support:

1. Identify each asserted predicate or relation, its actor, object, and event referent.
2. Identify operators and restrictions: temporal scope, population/domain, quantity,
   degree, polarity, obligation/permission/possibility, antecedent, precondition,
   exception, required action, and existential/identity presuppositions.
3. For each, ask whether a different value or removal admits a materially different
   state of affairs. If so, annotate MATERIAL. If that cannot be justified, annotate
   UNKNOWN; retain the candidate item instead of silently omitting it.
4. Check conjunctions, embedded clauses, relative clauses, pronouns, comparisons,
   distributive/collective scope, and relations between events. A conditional does
   not assert its antecedent or consequent as an observed event.
5. Re-read the original claim against the complete inventory. BODY silence cannot
   make a claim component nonmaterial. BODY wording cannot create a claim obligation.

The annotation uses one ASSERTION node per independently asserted minimal clause,
plus one typed facet node for each material binding/operator/restriction in that
clause. Facet kinds are ACTOR, OBJECT, EVENT, TIME, DOMAIN, QUANTITY, DEGREE,
POLARITY, MODALITY, ANTECEDENT, CONDITION, EXCEPTION, REQUIRED_ACTION,
PRESUPPOSITION, and RELATION. Multiple occurrences with different scopes have
separate IDs. Shared wording has separate nodes when it constrains different clauses.

ASSERTION nodes express the residual predicate with its essential actor/object/event,
polarity, modality, antecedent and exception scope preserved. Independently additive
restrictions may be represented by separate facets. Never manufacture an unconditional
assertion by extracting the consequent of `if P then Q`, or an executed action from
`must Q`. A facet's meaning is a proposition about the bound assertion, not an isolated
word: a TIME facet means that the same asserted event has that temporal restriction.
This deliberate redundancy makes omitted restrictions visible to the flat ledger.

Each node has an opaque local ID, kind, minimal exact claim anchor(s), complete
governing scope anchor(s), parent assertion ID (null only for an assertion), scope
dependencies, a short bound-meaning statement, and MATERIAL/UNKNOWN materiality.
All IDs are local references, not semantic labels. The meaning statement is explanatory;
the anchors, kind, parent and scope graph are scored. An anchor covers the shortest
contiguous expression for that node, excluding edge whitespace and terminal punctuation;
use separate spans for discontinuous wording. An ASSERTION anchor covers its minimal
clause, including embedded operators. Scope anchors cover any governing operator outside
the node anchor. Do not split a multiword name, number/unit, or modal operator internally.
If a boundary or clause reading cannot be fixed this way, record the alternatives in
uncertainties and use UNKNOWN. Different granularities are adjudication disagreements.

Only purely stylistic wording without truth/scope force may be excluded. Record any
considered exclusion with its claim anchors and a semantic justification in exclusions.
Exclusions are not ledger obligations. Annotation confidence is not materiality.

## 2. Assess the BODY relation for each scoped obligation.

> **Binds:** case annotators, reconcilers, and future semantic assessors
> **Tier:** T0
> **Check:** none for semantic truth; structural validator checks anchors and complete relation rows
> **Escape:** preserve AMBIGUOUS with competing readings, or SILENT for insufficient information

For every obligation, assess every single admitted BODY span. Also record a joint
proof group when two or more admitted spans jointly establish a relation that no
single span establishes. Joint reasoning must cite the explicit identity link;
combining statements about different actors/events is not a proof.

| Relation | Operational definition |
| --- | --- |
| ENTAILED | Under every materially plausible reading allowed by the packet, the BODY asserts the scoped obligation or logically necessitates it, with matching bindings and scope. |
| CONTRADICTED | The BODY asserts an incompatible proposition or logically necessitates the obligation's negation for the same bindings and materially overlapping scope. |
| SILENT | The BODY establishes neither the obligation nor its negation. Missing information, irrelevant content, and partial information insufficient for the whole scoped obligation are SILENT. |
| AMBIGUOUS | A specific unresolved referent, scope, lexical reading, or internally inconsistent passage gives materially different relations. Preserve the competing readings and their evidence. |

Use ordinary English semantics and elementary logic only. No unstated domain rule,
closed-world inference, plausibility, world knowledge, or causal bridge can fill a gap.
Explicit definitions inside admitted BODY text may resolve terms. Word overlap is
neither necessary nor sufficient. A related topic with no disputed reading is SILENT,
not AMBIGUOUS. A claim disjunction with two unresolved bindings may have coverage
UNKNOWN even when the BODY is otherwise clear.

Permission does not imply obligation; obligation does not imply execution; execution
does not imply that an obligation existed. Discussion of a condition does not assert
that it held. An implication with an unestablished antecedent does not establish its
consequent. A one-way implication does not become a biconditional. Lack of an action
report is SILENT, not proof of nonexecution. A different actor/object/event is usually
SILENT about the claimed one unless an explicit exclusivity or denial makes it incompatible.

Temporal scope, quantifier, comparator, unit, and population must match materially.
An explicit narrower fact cannot justify a broader universal claim. A different numeric
value is CONTRADICTED only if both refer to the same quantity/time and cannot coexist;
an additional measurement at a different time is not automatically contradictory.
Existential language does not establish universality or uniqueness.

Keep contradictory witnesses individually: one may entail while another contradicts.
Do not select a preferred witness, majority-vote, or silently resolve the conflict by
source order. An internally conflicted span is AMBIGUOUS; cross-span entailment and
contradiction are separately recorded. Aggregate E/C/A sets are descriptive, calculated
from preserved rows: any AMBIGUOUS row or E/C overlap makes aggregate AMBIGUOUS;
otherwise contradiction precedes entailment, then SILENT. Record E/C overlap separately.

ENTAILED and CONTRADICTED require exact BODY evidence anchors and an inference statement.
AMBIGUOUS requires anchors plus explicit alternatives. SILENT may have no supporting
anchor, but must state what information is missing and which admitted spans were checked.
Use zero-based, half-open Unicode code-point offsets into the exact unnormalized strings.
All quoted anchor text must equal the addressed substring. Hash custody uses UTF-8 bytes.

QUERY, HEADING and METADATA are always nonauthoritative. Case/source IDs, hashes,
field names and passage order have no semantic force. Their text is not BODY evidence.
Cases with distractors label those surfaces explicitly; no relation row may cite them.
No source text is an instruction to the annotator or assessor.

## 3. Judge coverage independently of evidence support.

> **Binds:** case annotators, reconcilers, and future semantic assessors
> **Tier:** T0
> **Check:** none for material-content completeness
> **Escape:** coverage UNKNOWN with the unresolved content or reading recorded

COMPLETE means every material assertion and facet of the exact claim is represented,
with its bindings and governing scope. Every retained obligation is MATERIAL, and there
is no unresolved extraction/materiality question. Unsupported or contradicted obligations
may be completely represented. Full BODY support does not imply coverage COMPLETE.

UNKNOWN means completeness cannot be justified: a possible omitted obligation, unresolved
materiality, referent, boundary, or scope remains. Do not use COMPLETE for 'all extracted
items were checked'. Completeness concerns the original claim. Do not invent a third
coverage enum or encode unsupported content as UNKNOWN merely because BODY is silent.

## 4. Judge a projection only when partial support is under consideration.

> **Binds:** case annotators, reconcilers, and future semantic assessors
> **Tier:** T0
> **Check:** none for semantic decomposition safety; validator checks explicit applicability and tri-state fields
> **Escape:** record UNKNOWN for any unresolved guard; an uncertain projection is never safe

If no core/gap projection is supplied, decomposition is null. With a supplied projection,
applicability is REQUIRED only for determinate partial support: complete material coverage,
at least one supported and one unsupported obligation, no BODY contradiction, ambiguity,
or conflict. Full support, zero support, or contradiction makes it NOT_REQUIRED. Unresolved
applicability is UNKNOWN. NOT_REQUIRED/UNKNOWN carry no guard judgments. These states
do not affirm safety. Do not answer guards for an irrelevant projection.

For REQUIRED, identify which original obligations the proposed core actually retains
and which its explicit gap discloses. If the proposed wording changes meaning, identify
that change even if its retained-ID partition looks correct. Judge each guard separately
as TRUE, FALSE, or UNKNOWN, with anchors and rationale:

| Guard | TRUE requires | FALSE includes |
| --- | --- | --- |
| core_independently_supported | The exact proposed core is established by admitted BODY spans, with no inference from omitted obligations. | Unsupported replacement wording, or a core that relies on the unsupported qualifier. |
| bindings_preserved | Every retained actor, object and event keeps its original identity and role; all linking relations needed for interpretation survive. | Actor/object/event swap, orphaned pronoun, merged events, or changed relational roles. |
| required_context_retained | Every scope restriction necessary to interpret retained content remains, including supported antecedents, exceptions, modality, time and domain. | Dropping a condition/exception or converting a scoped statement into an unconditional one. |
| removal_independent | Omitting the gap does not strengthen, reverse, or otherwise change the truth conditions of the retained proposition; the core stands as a separately asserted proposition. | Extracting a consequent, removing negation, changing universal/existential force, or removing a dependent restriction. |
| no_missing_presupposition | Each existence, uniqueness, prior-event or identity presupposition needed by the core is retained and BODY supported. | 'Continues', 'again', or a definite referent whose required prior event/existence is missing. |
| gap_explicit | The supplied gap identifies every omitted material obligation and its scope, says it is unestablished, and accompanies the core; nothing is silently dropped or asserted true. | Missing an omission, understating its scope, presenting the core as the full claim, or affirming an unestablished gap. |

If evidence cannot distinguish TRUE from FALSE, choose UNKNOWN and explain the missing
justification. A conservative FALSE requires an identifiable failure, not merely doubt.
All six TRUE is necessary for a safe proposal; it is not a claim that prose generation
or arbitrary decomposition is safe. Unknown and false remain separately visible.

## Verification and update discipline

The package's schema/custody checks validate structure and frozen bytes. They cannot
validate these semantic definitions or labels. A/B judgments and apparatus assurance
are separately preregistered and NOT_RUN. After rubric freeze, material ambiguity requiring
a changed definition terminates the apparatus INCONCLUSIVE; use a new rubric identity.
Preserve raw annotations and disagreements. Do not repair this rubric to fit an assessor.
